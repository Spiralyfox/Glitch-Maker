# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "time_stretch"
EFFECT_ICON    = "T"
EFFECT_COLOR   = "#c74b50"
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
        super().__init__("Time Stretch", p)
        self.f = _slider_float(self._lo, "Factor (>1 slower, <1 faster)", 0.1, 4, 1.0, 0.1, 2, "x", 100)
        self._finish()
    def get_params(self): return {"factor": self.f.value()}
    def set_params(self, p): self.f.setValue(p.get("factor", 1.0))
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

from scipy.signal import resample as scipy_resample

def process(audio_data, start, end, sr=44100, **kw):
    before = audio_data[:start].copy(); segment = audio_data[start:end].copy(); after = audio_data[end:].copy()
    if len(segment) == 0: return audio_data.copy()
    new_len = max(64, int(len(segment) * kw.get("factor", 1.0)))
    if segment.ndim == 1: stretched = scipy_resample(segment, new_len).astype(np.float32)
    else:
        channels = [scipy_resample(segment[:, ch], new_len) for ch in range(segment.shape[1])]
        stretched = np.column_stack(channels).astype(np.float32)
    n = min(64, len(stretched) // 2)
    if n > 0:
        fi = np.linspace(0, 1, n, dtype=np.float32); fo = np.linspace(1, 0, n, dtype=np.float32)
        if stretched.ndim == 1: stretched[:n] *= fi; stretched[-n:] *= fo
        else:
            for ch in range(stretched.shape[1]): stretched[:n, ch] *= fi; stretched[-n:, ch] *= fo
    return np.concatenate([before, stretched, after], axis=0)
