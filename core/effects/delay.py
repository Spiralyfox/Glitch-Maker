"""
Delay — Echo avec feedback, modes ping-pong et sync BPM.
Filtre dans la boucle de feedback pour des echos qui s'assombrissent naturellement.
"""

import numpy as np
from scipy.signal import lfilter

# Diviseurs de note pour le sync BPM (en fractions de beat/quarter note)
_NOTE_DIVS = {
    "1/1": 4.0, "1/2": 2.0, "1/2d": 3.0,
    "1/4": 1.0, "1/4d": 1.5, "1/4t": 2/3,
    "1/8": 0.5, "1/8d": 0.75, "1/8t": 1/3,
    "1/16": 0.25, "1/16d": 0.375, "1/16t": 1/6,
    "1/32": 0.125,
}


def delay(audio_data: np.ndarray, start: int, end: int,
          delay_ms: float = 300.0, feedback: float = 0.4,
          mix: float = 0.5, sr: int = 44100,
          mode: str = "normal", sync_bpm: float = 0.0,
          sync_note: str = "1/4", filter_tone: float = 1.0) -> np.ndarray:
    """Delay avec feedback, ping-pong stereo, sync BPM et filtre de feedback.
    delay_ms: temps de delay manuel (ignore si sync_bpm > 0)
    feedback: quantite de re-injection (0.0-0.95)
    mix: dry/wet
    mode: 'normal' ou 'ping_pong' (alterne L/R)
    sync_bpm: si > 0, calcule le delay depuis le BPM
    sync_note: division de note ('1/4', '1/8', '1/8d', '1/16'...)
    filter_tone: filtre passe-bas dans le feedback (0=sombre, 1=brillant)
    """
    result = audio_data.copy()
    segment = result[start:end].copy().astype(np.float64)
    if len(segment) == 0:
        return result

    # Calcul du delay en samples
    if sync_bpm > 0:
        beat_dur = 60.0 / sync_bpm  # duree d'un quarter note en secondes
        note_mult = _NOTE_DIVS.get(sync_note, 1.0)
        actual_ms = beat_dur * note_mult * 1000.0
    else:
        actual_ms = delay_ms
    delay_samples = max(1, int(actual_ms * sr / 1000.0))
    feedback = max(0.0, min(0.95, feedback))

    n = len(segment)
    is_stereo = segment.ndim == 2

    # Assurer le stereo pour le ping-pong
    if mode == "ping_pong" and not is_stereo:
        segment = np.column_stack([segment, segment])
        is_stereo = True

    output = segment.copy()
    n_echoes = int(np.log(0.01) / np.log(max(feedback, 0.01))) + 1
    n_echoes = min(n_echoes, 40)

    # Coefficients du filtre 1-pole lowpass pour le feedback
    use_filter = filter_tone < 0.95
    if use_filter:
        alpha = filter_tone * 0.99
        b_filt = np.array([1.0 - alpha])
        a_filt = np.array([1.0, -alpha])

    # Appliquer chaque echo
    for i in range(1, n_echoes + 1):
        offset = i * delay_samples
        if offset >= n:
            break
        gain = feedback ** i
        if gain < 0.01:
            break

        echo_len = min(n - offset, n)
        echo_sig = segment[:echo_len] * gain

        # Appliquer le filtre de feedback (cumule a chaque echo)
        if use_filter:
            for _ in range(i):  # filtrer i fois = plus sombre pour les echos lointains
                if is_stereo:
                    for ch in range(echo_sig.shape[1]):
                        echo_sig[:, ch] = lfilter(b_filt, a_filt, echo_sig[:, ch])
                else:
                    echo_sig = lfilter(b_filt, a_filt, echo_sig)

        # Mode ping-pong : alterner gauche/droite
        if mode == "ping_pong" and is_stereo:
            if i % 2 == 1:
                # Echo a droite uniquement
                output[offset:offset + echo_len, 1] += echo_sig[:, 0] if echo_sig.ndim == 2 else echo_sig
            else:
                # Echo a gauche uniquement
                output[offset:offset + echo_len, 0] += echo_sig[:, 0] if echo_sig.ndim == 2 else echo_sig
        else:
            output[offset:offset + echo_len] += echo_sig

    # Reconvertir si on a force le stereo
    original_seg = result[start:end].copy().astype(np.float64)
    if mode == "ping_pong" and original_seg.ndim == 1:
        original_seg = np.column_stack([original_seg, original_seg])

    # Mix dry/wet
    mixed = original_seg * (1.0 - mix) + output * mix
    result_out = audio_data.copy()

    # Si on a elargi en stereo, il faut reconstruire le resultat
    if mode == "ping_pong" and audio_data[start:end].ndim == 1:
        # Convertir tout l'audio en stereo
        if audio_data.ndim == 1:
            result_out = np.column_stack([audio_data.copy(), audio_data.copy()])
        else:
            result_out = audio_data.copy()
        result_out[start:end] = mixed.astype(np.float32)
    else:
        result_out[start:end] = mixed.astype(np.float32)

    return np.clip(result_out, -1.0, 1.0)
