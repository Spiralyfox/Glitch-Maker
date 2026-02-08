"""
Vocal Chop — Rhythmic gate that chops audio into patterns.
Essential for digicore/hyperpop vocal edits.
"""
import numpy as np
from core.effects.utils import apply_micro_fade

_PATTERNS = {
    "straight":  [1,0,1,0,1,0,1,0],
    "dotted":    [1,1,0,1,1,0,1,0],
    "triplet":   [1,0,1,0,0,1,0,1,0,0,1,0],
    "glitch":    [1,1,0,0,1,0,1,1,0,1,0,0,1,1,1,0],
    "staccato":  [1,0,0,0,1,0,0,0],
    "syncopated":[0,1,1,0,0,1,0,1],
    "chaos":     [1,0,1,1,0,0,1,0,0,1,1,1,0,1,0,0],
    "rapid":     [1,0,1,0,1,0,1,0,1,0,1,0,1,0,1,0],
}


def vocal_chop(audio_data, start, end, sr=44100,
               bpm=140, pattern="glitch", gate_shape=0.8,
               pitch_variation=0.0, reverse_hits=False):
    """
    Rhythmic gate chopping.
    bpm: tempo for the pattern
    pattern: predefined rhythm pattern
    gate_shape: 0=very short chops, 1=full length
    pitch_variation: random pitch shift per chop
    reverse_hits: reverse every other chop
    """
    result = audio_data.copy()
    seg = result[start:end].copy().astype(np.float64)
    n = len(seg)
    if n < 64:
        return result
    is_stereo = seg.ndim == 2

    pat = _PATTERNS.get(pattern, _PATTERNS["glitch"])
    pat_len = len(pat)

    # Duration of one pattern step in samples
    beat_samples = int(60.0 / bpm * sr)  # quarter note
    step_samples = beat_samples // 4  # sixteenth note
    step_samples = max(64, step_samples)

    # Build gate envelope
    gate = np.zeros(n, dtype=np.float64)
    chop_regions = []  # (start, end) of active regions

    for i in range(0, n, step_samples):
        pat_idx = (i // step_samples) % pat_len
        if pat[pat_idx] == 1:
            active_len = int(step_samples * gate_shape)
            active_len = max(16, active_len)
            end_pos = min(i + active_len, n)
            gate[i:end_pos] = 1.0
            # Micro fade in/out for click-free
            fade = min(32, active_len // 4)
            if fade > 0:
                gate[i:i + fade] *= np.linspace(0, 1, fade)
                if end_pos - fade > i:
                    gate[end_pos - fade:end_pos] *= np.linspace(1, 0, fade)
            chop_regions.append((i, end_pos))

    # Apply gate
    if is_stereo:
        seg *= gate[:, np.newaxis]
    else:
        seg *= gate

    # Reverse every other hit
    if reverse_hits:
        for idx, (cs, ce) in enumerate(chop_regions):
            if idx % 2 == 1 and ce <= n:
                if is_stereo:
                    seg[cs:ce] = seg[cs:ce][::-1]
                else:
                    seg[cs:ce] = seg[cs:ce][::-1]

    # Pitch variation per chop
    if pitch_variation > 0.01:
        from scipy.signal import resample as sp_resample
        rng = np.random.RandomState(42)
        for cs, ce in chop_regions:
            chop_len = ce - cs
            if chop_len < 32:
                continue
            shift = rng.uniform(-pitch_variation, pitch_variation)
            factor = 2.0 ** (shift * 2 / 12.0)  # up to ±2 semitones
            new_len = max(2, int(chop_len / factor))
            if is_stereo:
                for ch in range(seg.shape[1]):
                    chunk = seg[cs:ce, ch]
                    shifted = sp_resample(chunk, new_len)
                    shifted = sp_resample(shifted, chop_len)
                    seg[cs:ce, ch] = shifted
            else:
                chunk = seg[cs:ce]
                shifted = sp_resample(chunk, new_len)
                shifted = sp_resample(shifted, chop_len)
                seg[cs:ce] = shifted

    result[start:end] = apply_micro_fade(seg.astype(np.float32), 64)
    return np.clip(result, -1.0, 1.0)
