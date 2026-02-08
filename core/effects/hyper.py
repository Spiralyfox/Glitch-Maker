"""
Hyper — Hyperpop / digicore multi-effect chain.
Combines compression, saturation, pitch shimmer, and brightness.
One-knob "make it hyperpop" effect.
"""
import numpy as np
from core.effects.utils import apply_micro_fade


def hyper(audio_data, start, end, sr=44100,
          intensity=0.6, shimmer=0.3, brightness=0.5, crush=0.0, width=0.5):
    """
    Hyperpop multi-effect.
    intensity: overall drive/compression amount
    shimmer: pitched-up octave layer mixed in
    brightness: high-frequency boost
    crush: bit-crush amount for digital texture
    width: stereo widening
    """
    result = audio_data.copy()
    seg = result[start:end].copy().astype(np.float64)
    n = len(seg)
    if n < 64:
        return result
    is_stereo = seg.ndim == 2

    # ── 1. Compression (soft-knee limiter) ──
    threshold = 1.0 - intensity * 0.6  # lower threshold = more compression
    ratio = 1.0 + intensity * 7.0  # up to 8:1
    if is_stereo:
        for ch in range(seg.shape[1]):
            _compress_channel(seg[:, ch], threshold, ratio)
    else:
        _compress_channel(seg, threshold, ratio)

    # ── 2. Saturation (warm overdrive) ──
    if intensity > 0.1:
        drive = 1.0 + intensity * 4.0
        seg = np.tanh(seg * drive) / np.tanh(drive)

    # ── 3. Shimmer (octave-up layer) ──
    if shimmer > 0.01:
        from scipy.signal import resample
        if is_stereo:
            mono = np.mean(seg, axis=1)
        else:
            mono = seg.copy()
        # Create octave-up version
        half_len = max(2, n // 2)
        octave = resample(mono, half_len)
        octave = resample(octave, n)
        # Create fifth-up version (1.5x freq)
        fifth_len = max(2, int(n / 1.5))
        fifth = resample(mono, fifth_len)
        fifth = resample(fifth, n)
        shimmer_layer = 0.6 * octave + 0.4 * fifth
        shimmer_layer *= shimmer * 0.4
        if is_stereo:
            seg[:, 0] += shimmer_layer
            seg[:, 1] += shimmer_layer
        else:
            seg += shimmer_layer

    # ── 4. Brightness (high shelf boost) ──
    if brightness > 0.01:
        # Simple high-frequency emphasis via differentiation + mix
        if is_stereo:
            for ch in range(seg.shape[1]):
                diff = np.diff(seg[:, ch], prepend=seg[0, ch])
                seg[:, ch] += diff * brightness * 0.3
        else:
            diff = np.diff(seg, prepend=seg[0])
            seg += diff * brightness * 0.3

    # ── 5. Bit crush layer ──
    if crush > 0.05:
        levels = max(8, int(512 * (1.0 - crush * 0.85)))
        crushed = np.round(seg * levels) / levels
        seg = seg * (1.0 - crush) + crushed * crush

    # ── 6. Stereo widening ──
    if is_stereo and width > 0.01:
        mid = (seg[:, 0] + seg[:, 1]) * 0.5
        side = (seg[:, 0] - seg[:, 1]) * 0.5
        side *= (1.0 + width * 2.0)
        seg[:, 0] = mid + side
        seg[:, 1] = mid - side

    # Final limiter
    seg = np.tanh(seg * 0.95)

    result[start:end] = apply_micro_fade(seg.astype(np.float32), 64)
    return np.clip(result, -1.0, 1.0)


def _compress_channel(data, threshold, ratio):
    """In-place soft-knee compression."""
    abs_data = np.abs(data)
    mask = abs_data > threshold
    if np.any(mask):
        excess = abs_data[mask] - threshold
        compressed = threshold + excess / ratio
        signs = np.sign(data[mask])
        data[mask] = signs * compressed
