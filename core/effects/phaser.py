"""Phaser — sweeps notch filters through the signal for a whooshing effect."""
import numpy as np

def phaser(audio_data: np.ndarray, start: int, end: int,
           rate_hz: float = 0.5, depth: float = 0.7,
           stages: int = 4, mix: float = 0.7, sr: int = 44100) -> np.ndarray:
    out = audio_data.copy()
    seg = out[start:end].astype(np.float64)
    n = len(seg)
    if seg.ndim == 1:
        seg = seg.reshape(-1, 1)
    channels = seg.shape[1]
    result = seg.copy()
    t_arr = np.arange(n, dtype=np.float64) / sr
    lfo = 0.5 * (1.0 + np.sin(2.0 * np.pi * rate_hz * t_arr)) * depth
    for ch in range(channels):
        x = seg[:, ch].copy()
        for stage in range(stages):
            freq = 200.0 + 3000.0 * lfo + stage * 100.0
            omega = 2.0 * np.pi * freq / sr
            alpha = (1.0 - np.tan(np.clip(omega / 2, 0.001, np.pi * 0.49))) / \
                    (1.0 + np.tan(np.clip(omega / 2, 0.001, np.pi * 0.49)))
            y = np.zeros(n)
            prev_x, prev_y = 0.0, 0.0
            for i in range(n):
                a = alpha[i] if hasattr(alpha, '__len__') else alpha
                y[i] = a * x[i] + prev_x - a * prev_y
                prev_x, prev_y = x[i], y[i]
            x = y
        result[:, ch] = seg[:, ch] * (1 - mix) + x * mix
    out[start:end] = result.astype(np.float32)
    if out[start:end].ndim != audio_data[start:end].ndim:
        out[start:end] = result.squeeze().astype(np.float32)
    return out
