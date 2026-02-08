# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "volume"
EFFECT_ICON    = "U"
EFFECT_COLOR   = "#4cc9f0"
EFFECT_SECTION = "Basics"

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
        super().__init__("Volume", p)
        self.inp = _slider_int(self._lo, "Gain (%)", 0, 1000, 100, " %")
        self._finish()
    def get_params(self): return {"gain_pct": self.inp.value()}
    def set_params(self, p): self.inp.setValue(int(p.get("gain_pct", 100)))
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

def process(audio_data, start, end, sr=44100, **kw):
    out = audio_data.copy()
    g = kw.get("gain_pct", 100) / 100.0
    out[start:end] = (out[start:end] * g).clip(-1.0, 1.0)
    return out
