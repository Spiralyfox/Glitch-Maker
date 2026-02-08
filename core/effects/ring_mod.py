"""
Ring Modulator — Multiplie le signal par une onde sinusoidale.
Produit des sons metalliques, robotiques, inharmoniques.
"""

import numpy as np


def ring_mod(audio_data: np.ndarray, start: int, end: int,
             freq: float = 440.0, mix: float = 0.7,
             sr: int = 44100) -> np.ndarray:
    """Applique une modulation en anneau sur la zone."""
    result = audio_data.copy()
    segment = result[start:end].copy()
    if len(segment) == 0:
        return result

    # Generer la porteuse sinusoidale
    t = np.arange(len(segment), dtype=np.float32) / sr
    carrier = np.sin(2.0 * np.pi * freq * t).astype(np.float32)

    # Appliquer la modulation
    if segment.ndim == 1:
        modulated = segment * carrier
    else:
        modulated = segment.copy()
        for ch in range(segment.shape[1]):
            modulated[:, ch] = segment[:, ch] * carrier

    # Mix dry/wet
    result[start:end] = segment * (1.0 - mix) + modulated * mix
    return np.clip(result, -1.0, 1.0)
