"""
Filtre Resonant — Low-pass / High-pass avec cutoff et resonance.
Peut aussi faire un sweep (balayage) automatique.
"""

import numpy as np
from scipy.signal import butter, sosfilt


def resonant_filter(audio_data: np.ndarray, start: int, end: int,
                    filter_type: str = "lowpass", cutoff: float = 2000.0,
                    resonance: float = 1.0, sweep: bool = False,
                    sr: int = 44100, zi=None) -> np.ndarray:
    """Filtre LP ou HP avec cutoff et resonance (Q).

    If zi is provided, returns (result, zf) for stateful processing.
    Otherwise returns just result for backward compatibility.
    """
    result = audio_data.copy()
    segment = result[start:end].copy()
    if len(segment) == 0:
        if zi is not None:
            return result, zi
        return result

    # Clamp le cutoff pour eviter les erreurs de Nyquist
    nyquist = sr / 2.0
    cutoff = max(20.0, min(cutoff, nyquist * 0.95))

    if sweep:
        # Sweep : applique le filtre par chunks avec cutoff variable
        output = _apply_sweep(segment, filter_type, cutoff, resonance, sr)
        result[start:end] = output
        if zi is not None:
            return np.clip(result, -1.0, 1.0), None
        return np.clip(result, -1.0, 1.0)

    # Stateful filter
    output, zf = _apply_filter(segment, filter_type, cutoff, resonance, sr, zi=zi)

    result[start:end] = output
    if zi is not None:
        return np.clip(result, -1.0, 1.0), zf
    return np.clip(result, -1.0, 1.0)


def _apply_filter(segment, ftype, cutoff, Q, sr, zi=None):
    """Applique un filtre Butterworth statique.
    Returns (output, zf) tuple.
    """
    nyquist = sr / 2.0
    norm_cutoff = cutoff / nyquist
    norm_cutoff = max(0.001, min(0.999, norm_cutoff))

    # Ordre du filtre depend de la resonance
    order = max(2, min(8, int(Q * 2)))
    btype = "low" if ftype == "lowpass" else "high"
    sos = butter(order, norm_cutoff, btype=btype, output="sos")

    if segment.ndim == 1:
        if zi is None:
            zi = np.zeros((sos.shape[0], 2), dtype=np.float64)
        res, zf = sosfilt(sos, segment, zi=zi)
        return res.astype(np.float32), zf
    else:
        out = segment.copy()
        n_ch = segment.shape[1]
        if zi is None:
            zi = [np.zeros((sos.shape[0], 2), dtype=np.float64) for _ in range(n_ch)]
        new_zi = []
        for ch in range(n_ch):
            ch_zi = zi[ch] if ch < len(zi) else np.zeros((sos.shape[0], 2), dtype=np.float64)
            res_ch, zf_ch = sosfilt(sos, segment[:, ch], zi=ch_zi)
            out[:, ch] = res_ch.astype(np.float32)
            new_zi.append(zf_ch)
        return out, new_zi


def _apply_sweep(segment, ftype, cutoff, Q, sr):
    """Applique un sweep de filtre (cutoff monte puis descend)."""
    n_chunks = 32
    chunk_size = max(256, len(segment) // n_chunks)
    output = np.zeros_like(segment)
    nyquist = sr / 2.0

    for i in range(n_chunks):
        s = i * chunk_size
        e = min(s + chunk_size, len(segment))
        if s >= len(segment):
            break

        # Cutoff varie en sinus (monte et descend)
        progress = i / max(n_chunks - 1, 1)
        sweep_mult = 0.5 + 0.5 * np.sin(progress * np.pi * 2)
        sweep_cutoff = max(60.0, cutoff * (0.2 + sweep_mult * 1.6))
        sweep_cutoff = min(sweep_cutoff, nyquist * 0.95)

        chunk = segment[s:e].copy()
        filtered, _ = _apply_filter(chunk, ftype, sweep_cutoff, Q, sr)
        output[s:e] = filtered

    return output

