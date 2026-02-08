# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "tape_stop"
EFFECT_ICON    = "X"
EFFECT_COLOR   = "#3d5a80"
EFFECT_SECTION = "Pitch & Time"

# ══════════════════════════════════════════════════
# Dialog (UI for effect parameters)
# ══════════════════════════════════════════════════
import numpy as np
from PyQt6.QtWidgets import QLabel, QComboBox, QCheckBox, QHBoxLayout, QDial
from PyQt6.QtCore import Qt
from gui.effect_dialogs import _Base, _slider_int, _slider_float, _btn
from utils.config import COLORS

class Dialog(_Base):
    def __init__(self, p=None):
        super().__init__("Tape Stop", p)
        self.d = _slider_int(self._lo, "Duration (ms)", 100, 5000, 1500, " ms")
        self._finish()
    def get_params(self): return {"duration_ms": self.d.value()}
    def set_params(self, p): self.d.setValue(int(p.get("duration_ms", 1500)))
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

from scipy.signal import resample as scipy_resample

def process(audio_data, start, end, sr=44100, **kw):
    result = audio_data.copy(); segment = result[start:end].copy()
    if len(segment) == 0: return result
    seg_len = len(segment)
    duration_ms = kw.get("duration_ms", 1500)
    duration_pct = min(1.0, max(0.05, (duration_ms / 1000.0) * sr / seg_len)) if seg_len > 0 else 0.5
    effect_len = max(256, int(seg_len * duration_pct))
    clean_len = max(0, seg_len - effect_len)
    effect_len = seg_len - clean_len
    clean_part = segment[:clean_len].copy(); effect_part = segment[clean_len:].copy()
    n_chunks = 64; chunk_size = max(1, len(effect_part) // n_chunks); output_chunks = []
    for i in range(n_chunks):
        s = i * chunk_size; e = min(s + chunk_size, len(effect_part))
        if s >= len(effect_part): break
        chunk = effect_part[s:e].copy()
        speed = max(0.05, 1.0 - (i / n_chunks) * 0.95)
        new_len = max(4, int(len(chunk) / speed))
        if chunk.ndim == 1: stretched = scipy_resample(chunk, new_len).astype(np.float32)
        else:
            cols = [scipy_resample(chunk[:, ch], new_len) for ch in range(chunk.shape[1])]
            stretched = np.column_stack(cols).astype(np.float32)
        stretched *= max(0.0, 1.0 - (i / n_chunks) * 0.8)
        output_chunks.append(stretched)
    effect_out = np.concatenate(output_chunks, axis=0) if output_chunks else effect_part
    combined = np.concatenate([clean_part, effect_out], axis=0)
    if len(combined) > seg_len: combined = combined[:seg_len]
    elif len(combined) < seg_len:
        combined = np.concatenate([combined, np.zeros((seg_len - len(combined),) + combined.shape[1:], dtype=np.float32)], axis=0)
    result[start:end] = combined
    return result
