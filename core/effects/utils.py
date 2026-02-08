"""
Fonctions DSP utilitaires communes a tous les effets.
Micro-fades, normalisation, fade in/out, crossfade.
"""

import numpy as np


def apply_micro_fade(audio: np.ndarray, fade_samples: int = 64) -> np.ndarray:
    """Micro fade-in/out anti-clic aux jointures."""
    result = audio.copy()
    n = min(fade_samples, len(result) // 2)
    if n == 0:
        return result
    fade_in = np.linspace(0, 1, n, dtype=np.float32)
    fade_out = np.linspace(1, 0, n, dtype=np.float32)
    if result.ndim == 1:
        result[:n] *= fade_in
        result[-n:] *= fade_out
    else:
        for ch in range(result.shape[1]):
            result[:n, ch] *= fade_in
            result[-n:, ch] *= fade_out
    return result


def normalize(audio: np.ndarray, target_peak: float = 0.95) -> np.ndarray:
    """Normalise au pic donne."""
    peak = np.max(np.abs(audio))
    if peak == 0:
        return audio
    return audio * (target_peak / peak)


def fade_in(audio: np.ndarray, duration_samples: int) -> np.ndarray:
    """Fade-in lineaire sur les N premiers samples."""
    result = audio.copy()
    n = min(duration_samples, len(result))
    if n <= 0:
        return result
    curve = np.linspace(0.0, 1.0, n, dtype=np.float32)
    if result.ndim == 1:
        result[:n] *= curve
    else:
        for ch in range(result.shape[1]):
            result[:n, ch] *= curve
    return result


def fade_out(audio: np.ndarray, duration_samples: int) -> np.ndarray:
    """Fade-out lineaire sur les N derniers samples."""
    result = audio.copy()
    n = min(duration_samples, len(result))
    if n <= 0:
        return result
    curve = np.linspace(1.0, 0.0, n, dtype=np.float32)
    if result.ndim == 1:
        result[-n:] *= curve
    else:
        for ch in range(result.shape[1]):
            result[-n:, ch] *= curve
    return result


def crossfade(audio_a: np.ndarray, audio_b: np.ndarray,
              overlap_samples: int) -> np.ndarray:
    """Fusionne deux segments avec un crossfade."""
    overlap = min(overlap_samples, len(audio_a), len(audio_b))
    if overlap <= 0:
        return np.concatenate([audio_a, audio_b], axis=0)
    fade_o = np.linspace(1.0, 0.0, overlap, dtype=np.float32)
    fade_i = np.linspace(0.0, 1.0, overlap, dtype=np.float32)
    part_a = audio_a[:-overlap].copy()
    mix_a = audio_a[-overlap:].copy()
    mix_b = audio_b[:overlap].copy()
    part_b = audio_b[overlap:].copy()
    if mix_a.ndim == 1:
        mixed = mix_a * fade_o + mix_b * fade_i
    else:
        mixed = np.zeros_like(mix_a)
        for ch in range(mix_a.shape[1]):
            mixed[:, ch] = mix_a[:, ch] * fade_o + mix_b[:, ch] * fade_i
    return np.concatenate([part_a, mixed, part_b], axis=0)
