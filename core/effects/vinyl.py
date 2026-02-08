"""
Vinyl Crackle — Ajoute du bruit de vinyle, crackle et artefacts.
Patine lo-fi nostalgique.
"""

import numpy as np
from scipy.signal import butter, sosfilt


def vinyl(audio_data: np.ndarray, start: int, end: int,
          crackle: float = 0.5, noise: float = 0.3,
          wow: float = 0.2, sr: int = 44100) -> np.ndarray:
    """Ajoute des artefacts vinyle : crackle, bruit, wow/flutter."""
    result = audio_data.copy()
    segment = result[start:end].copy()
    if len(segment) == 0:
        return result

    rng = np.random.default_rng()
    seg_len = len(segment)

    # 1) Crackle : impulsions aleatoires courtes
    if crackle > 0:
        crackle_signal = np.zeros(seg_len, dtype=np.float32)
        n_pops = int(seg_len * crackle * 0.001)  # Densite de pops
        pop_positions = rng.integers(0, seg_len, size=n_pops)
        pop_amplitudes = rng.uniform(0.02, 0.15, size=n_pops).astype(np.float32)
        pop_signs = rng.choice([-1.0, 1.0], size=n_pops).astype(np.float32)
        crackle_signal[pop_positions] = pop_amplitudes * pop_signs * crackle

        # Filtrer le crackle pour le rendre plus realiste (passe-haut)
        nyq = sr / 2.0
        sos = butter(2, min(1000.0 / nyq, 0.99), btype="high", output="sos")
        crackle_signal = sosfilt(sos, crackle_signal).astype(np.float32)

        if segment.ndim == 1:
            segment += crackle_signal
        else:
            for ch in range(segment.shape[1]):
                segment[:, ch] += crackle_signal

    # 2) Bruit de fond (hiss)
    if noise > 0:
        hiss = rng.normal(0, noise * 0.02, size=seg_len).astype(np.float32)
        # Filtrer : bruit surtout dans les hautes frequences
        nyq = sr / 2.0
        sos = butter(2, min(3000.0 / nyq, 0.99), btype="high", output="sos")
        hiss = sosfilt(sos, hiss).astype(np.float32)

        if segment.ndim == 1:
            segment += hiss
        else:
            for ch in range(segment.shape[1]):
                segment[:, ch] += hiss

    # 3) Wow/Flutter : variation lente de vitesse
    if wow > 0:
        t = np.arange(seg_len, dtype=np.float32) / sr
        # Variation sinusoidale lente (0.5-2 Hz)
        wow_signal = 1.0 + wow * 0.005 * np.sin(2 * np.pi * 1.5 * t)
        # Appliquer comme variation de phase (simplifiee)
        indices = np.cumsum(wow_signal).astype(np.float32)
        indices = indices / indices[-1] * (seg_len - 1)
        indices = np.clip(indices, 0, seg_len - 1).astype(int)

        if segment.ndim == 1:
            segment = segment[indices]
        else:
            segment = segment[indices]

    result[start:end] = np.clip(segment, -1.0, 1.0)
    return result
