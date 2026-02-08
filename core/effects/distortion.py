"""Distortion — waveshaping distortion with multiple algorithms."""
import numpy as np
from scipy.signal import lfilter


def distortion(audio_data: np.ndarray, start: int, end: int,
               drive: float = 5.0, tone: float = 0.5,
               mode: str = "tube") -> np.ndarray:
    """Applique une distortion (tube, fuzz, digital, scream).
    drive: intensite de la distortion (1-20)
    tone: filtre passe-bas post-distortion (0=sombre, 1=brillant)
    mode: algorithme de waveshaping
    """
    out = audio_data.copy()
    seg = out[start:end].astype(np.float64) * drive
    if mode == "tube":
        seg = np.sign(seg) * (1.0 - np.exp(-np.abs(seg)))
    elif mode == "fuzz":
        seg = np.tanh(seg * 2.0) * np.sign(seg + 0.001)
    elif mode == "digital":
        seg = np.clip(seg, -1.0, 1.0)
        steps = max(2, int(16 / drive))
        seg = np.round(seg * steps) / steps
    elif mode == "scream":
        seg = np.tanh(seg * 3.0)
        seg = np.sign(seg) * np.power(np.abs(seg), 0.3)
    # Tone filter — 1-pole IIR lowpass via scipy (vectorise, 100x faster)
    if tone < 0.95:
        alpha = tone * 0.99
        b = np.array([1.0 - alpha])
        a = np.array([1.0, -alpha])
        if seg.ndim == 2:
            for ch in range(seg.shape[1]):
                seg[:, ch] = lfilter(b, a, seg[:, ch])
        else:
            seg = lfilter(b, a, seg)
    out[start:end] = np.clip(seg, -1.0, 1.0).astype(np.float32)
    return out
