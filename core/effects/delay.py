"""
Delay Feedback — Echo avec feedback qui s'auto-alimente.
Pousse a fond, ca cree un chaos sonore type glitchcore.
"""

import numpy as np


def delay(audio_data: np.ndarray, start: int, end: int,
          delay_ms: float = 200.0, feedback: float = 0.6,
          mix: float = 0.5, sr: int = 44100) -> np.ndarray:
    """Applique un delay avec feedback sur la zone."""
    result = audio_data.copy()
    segment = result[start:end].copy()
    if len(segment) == 0:
        return result

    # Delay en samples
    delay_samples = max(1, int(delay_ms * sr / 1000.0))
    feedback = max(0.0, min(0.95, feedback))  # Cap a 0.95 pour eviter l'explosion

    # Buffer de sortie (meme taille que le segment)
    output = segment.copy()
    n_echoes = int(np.log(0.01) / np.log(max(feedback, 0.01))) + 1
    n_echoes = min(n_echoes, 30)  # Maximum 30 echos

    # Appliquer chaque echo
    for i in range(1, n_echoes + 1):
        offset = i * delay_samples
        if offset >= len(segment):
            break
        gain = feedback ** i
        if gain < 0.01:
            break

        # Ajouter l'echo decale
        echo_len = min(len(segment) - offset, len(segment))
        if segment.ndim == 1:
            output[offset:offset + echo_len] += segment[:echo_len] * gain
        else:
            output[offset:offset + echo_len] += segment[:echo_len] * gain

    # Mix dry/wet
    result[start:end] = segment * (1.0 - mix) + output * mix
    return np.clip(result, -1.0, 1.0)
