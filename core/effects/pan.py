"""Pan / Stereo — adjust stereo balance or convert to mono."""
import numpy as np


def pan_stereo(audio_data: np.ndarray, start: int, end: int,
               pan: float = 0.0, mono: bool = False) -> np.ndarray:
    """
    Pan audio left/right and optionally convert to mono.
    
    Args:
        pan: -1.0 (full left) to +1.0 (full right), 0 = center
        mono: if True, merge to mono (same signal on both channels)
    """
    out = audio_data.copy()
    seg = out[start:end].astype(np.float64)

    # Ensure stereo
    if seg.ndim == 1:
        seg = np.column_stack([seg, seg])
    elif seg.shape[1] == 1:
        seg = np.column_stack([seg[:, 0], seg[:, 0]])

    if mono:
        # Convert to mono: average both channels
        m = np.mean(seg[:, :2], axis=1)
        seg[:, 0] = m
        seg[:, 1] = m

    # Apply panning (constant power pan law)
    pan_val = np.clip(pan, -1.0, 1.0)
    # Angle in radians: -1 → 0, 0 → π/4, +1 → π/2
    angle = (pan_val + 1.0) * np.pi / 4.0
    gain_l = np.cos(angle)
    gain_r = np.sin(angle)

    seg[:, 0] *= gain_l
    seg[:, 1] *= gain_r

    out[start:end] = seg.astype(np.float32)
    if out[start:end].ndim != audio_data[start:end].ndim:
        out[start:end] = seg[:, :audio_data.shape[1] if audio_data.ndim > 1 else 1].astype(np.float32)
    return out
