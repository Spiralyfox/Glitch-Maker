"""
Effet Pitch Shift — Monte ou descend le pitch.
Voix "anime" digicore, ou grave/demonique.
Option preserve_formants pour eviter l'effet chipmunk.
"""

import numpy as np
from scipy.signal import resample
from core.effects.utils import apply_micro_fade


def _compensate_formants(signal, semitones, sr):
    """Compense le decalage des formants cause par le pitch shift.
    Applique un formant shift inverse : resample pour deplacer l'enveloppe
    spectrale dans la direction opposee, puis restaure la duree.
    """
    if abs(semitones) < 0.1:
        return signal
    n = len(signal)
    # Inverse formant shift: si on monte le pitch de +5, on descend les formants de -5
    factor = 2.0 ** (-semitones / 12.0)
    intermediate_len = max(2, int(n / factor))
    shifted = resample(signal, intermediate_len)
    return resample(shifted, n)


def pitch_shift(audio_data: np.ndarray, start: int, end: int,
                semitones: float = 3.0, sr: int = 44100,
                preserve_formants: bool = False) -> np.ndarray:
    """Change le pitch sans (trop) changer la duree.
    semitones: demi-tons (-24 a +24)
    preserve_formants: compense les formants pour eviter l'effet chipmunk
    """
    result = audio_data.copy()
    segment = result[start:end].copy()

    if len(segment) == 0:
        return result

    factor = 2.0 ** (semitones / 12.0)
    original_len = len(segment)
    new_len = int(original_len / factor)
    if new_len < 2:
        return result

    if segment.ndim == 1:
        shifted = resample(segment, new_len)
        shifted = resample(shifted, original_len)
        if preserve_formants:
            shifted = _compensate_formants(shifted, semitones, sr)
    else:
        channels = []
        for ch in range(segment.shape[1]):
            ch_shifted = resample(segment[:, ch], new_len)
            ch_shifted = resample(ch_shifted, original_len)
            if preserve_formants:
                ch_shifted = _compensate_formants(ch_shifted, semitones, sr)
            channels.append(ch_shifted)
        shifted = np.column_stack(channels)

    shifted = apply_micro_fade(shifted.astype(np.float32), fade_samples=64)
    result[start:end] = shifted[:len(result[start:end])]
    return np.clip(result, -1.0, 1.0)


def pitch_shift_simple(audio_data: np.ndarray, start: int, end: int,
                       semitones: float = 3.0, sr: int = 44100) -> np.ndarray:
    """Pitch shift simple (change aussi la duree) — effet chipmunk ou ralenti.
    Plus rapide et plus glitchy que le pitch shift corrige.
    """
    result_before = audio_data[:start].copy()
    segment = audio_data[start:end].copy()
    result_after = audio_data[end:].copy()

    if len(segment) == 0:
        return audio_data.copy()

    factor = 2.0 ** (semitones / 12.0)
    new_len = int(len(segment) / factor)
    if new_len < 2:
        return audio_data.copy()

    if segment.ndim == 1:
        shifted = resample(segment, new_len)
    else:
        channels = []
        for ch in range(segment.shape[1]):
            channels.append(resample(segment[:, ch], new_len))
        shifted = np.column_stack(channels)

    shifted = apply_micro_fade(shifted.astype(np.float32), fade_samples=64)
    return np.clip(np.concatenate([result_before, shifted, result_after], axis=0), -1.0, 1.0)
