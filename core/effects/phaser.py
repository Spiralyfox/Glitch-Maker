"""Phaser — cascaded allpass filters with LFO for a sweeping, whooshing effect."""
import numpy as np
from scipy.signal import lfilter


def phaser(audio_data: np.ndarray, start: int, end: int,
           rate_hz: float = 0.5, depth: float = 0.7,
           stages: int = 4, mix: float = 0.7, sr: int = 44100) -> np.ndarray:
    """
    Phaser effect using cascaded first-order allpass filters with LFO modulation.

    Args:
        rate_hz: LFO speed (0.05-10 Hz)
        depth: LFO depth (0-1)
        stages: number of allpass filter stages (1-12, more = deeper)
        mix: dry/wet mix (0-1)
        sr: sample rate
    """
    out = audio_data.copy()
    seg = out[start:end].astype(np.float64)
    n = len(seg)

    if n == 0:
        return out

    if seg.ndim == 1:
        seg = seg.reshape(-1, 1)
    channels = seg.shape[1]

    # Time array for LFO
    t_arr = np.arange(n, dtype=np.float64) / sr

    # LFO: sweeps between min and max frequency
    min_freq = 100.0
    max_freq = 4000.0
    lfo = min_freq + (max_freq - min_freq) * depth * 0.5 * (1.0 + np.sin(2.0 * np.pi * rate_hz * t_arr))

    # Process in blocks for time-varying filter coefficients
    block_size = max(64, sr // 100)  # ~10ms blocks
    n_blocks = (n + block_size - 1) // block_size

    result = np.zeros_like(seg)

    for ch in range(channels):
        x = seg[:, ch].copy()
        y = x.copy()

        for stage in range(stages):
            # Each stage offset slightly for richer effect
            stage_offset = stage * 200.0
            filtered = np.zeros(n)
            state = 0.0  # filter state

            for blk in range(n_blocks):
                s = blk * block_size
                e = min(s + block_size, n)
                block_len = e - s

                # Get center frequency for this block
                center_freq = lfo[s] + stage_offset
                center_freq = np.clip(center_freq, 20, sr / 2 - 100)

                # First-order allpass: H(z) = (a + z^-1) / (1 + a*z^-1)
                # where a = (tan(pi*f/sr) - 1) / (tan(pi*f/sr) + 1)
                omega = np.pi * center_freq / sr
                omega = np.clip(omega, 0.001, np.pi * 0.49)
                tan_w = np.tan(omega)
                a = (tan_w - 1.0) / (tan_w + 1.0)

                # Apply allpass filter to block
                b_coeff = np.array([a, 1.0])
                a_coeff = np.array([1.0, a])

                block_in = y[s:e]
                block_out, zf = lfilter(b_coeff, a_coeff, block_in, zi=np.array([state]))
                filtered[s:e] = block_out
                state = zf[0]

            y = filtered

        # Mix: dry * (1 - mix) + wet * mix
        result[:, ch] = seg[:, ch] * (1.0 - mix) + y * mix

    out[start:end] = result.astype(np.float32)
    if out[start:end].ndim != audio_data[start:end].ndim:
        out[start:end] = result.squeeze().astype(np.float32)
    return out
