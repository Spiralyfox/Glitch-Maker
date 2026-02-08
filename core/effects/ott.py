"""
OTT (Over The Top) — Compression multiband extreme.
LA signature sonore de l'hyperpop : ecrase la dynamique sur 3 bandes.
"""

import numpy as np
from scipy.signal import butter, sosfilt


def ott(audio_data: np.ndarray, start: int, end: int,
        depth: float = 0.7, sr: int = 44100) -> np.ndarray:
    """Compression multiband OTT sur la zone.
    depth: 0.0 = pas d'effet, 1.0 = compression max."""
    result = audio_data.copy()
    segment = result[start:end].copy()
    if len(segment) == 0:
        return result

    nyquist = sr / 2.0
    depth = max(0.0, min(1.0, depth))

    # Travailler en mono temporairement si stereo
    is_stereo = segment.ndim > 1 and segment.shape[1] >= 2
    if is_stereo:
        mono = np.mean(segment, axis=1)
    else:
        mono = segment.copy()

    # Separer en 3 bandes : low / mid / high
    low = _band_filter(mono, 0, 200, sr)
    mid = _band_filter(mono, 200, 5000, sr)
    high = _band_filter(mono, 5000, nyquist * 0.95, sr)

    # Compresser chaque bande agressivement
    low_c = _compress(low, threshold=0.1, ratio=8.0, depth=depth)
    mid_c = _compress(mid, threshold=0.08, ratio=10.0, depth=depth)
    high_c = _compress(high, threshold=0.05, ratio=12.0, depth=depth)

    # Recombiner
    combined = low_c + mid_c + high_c
    combined = np.clip(combined, -1.0, 1.0).astype(np.float32)

    # Remettre en stereo si necessaire
    if is_stereo:
        result[start:end, 0] = combined
        result[start:end, 1] = combined
    else:
        result[start:end] = combined

    return result


def _band_filter(audio, low_freq, high_freq, sr):
    """Extrait une bande de frequence."""
    nyquist = sr / 2.0
    low_n = max(0.001, low_freq / nyquist)
    high_n = min(0.999, high_freq / nyquist)

    if low_n <= 0.001:
        # Passe-bas uniquement
        sos = butter(4, high_n, btype="low", output="sos")
    elif high_n >= 0.999:
        # Passe-haut uniquement
        sos = butter(4, low_n, btype="high", output="sos")
    else:
        sos = butter(4, [low_n, high_n], btype="band", output="sos")

    return sosfilt(sos, audio).astype(np.float32)


def _compress(audio, threshold=0.1, ratio=8.0, depth=1.0):
    """Compression simple : reduit la dynamique au-dessus du seuil."""
    output = audio.copy()
    abs_signal = np.abs(output)

    # Ou le signal depasse le seuil
    mask = abs_signal > threshold
    if np.any(mask):
        # Gain reduction
        excess = abs_signal[mask] - threshold
        compressed_excess = excess / ratio
        target = threshold + compressed_excess

        # Appliquer avec le depth
        gain = np.ones_like(abs_signal)
        gain[mask] = target / (abs_signal[mask] + 1e-10)
        gain = 1.0 + (gain - 1.0) * depth

        output *= gain

    # Makeup gain (compenser la reduction)
    output *= (1.0 + depth * 2.0)
    return np.clip(output, -1.0, 1.0).astype(np.float32)
