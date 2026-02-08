# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "saturation"
EFFECT_ICON    = "D"
EFFECT_COLOR   = "#ff6b35"
EFFECT_SECTION = "Distortion"

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
        super().__init__("Saturation", p)
        self._row("Type"); self.tp = QComboBox(); self.tp.addItems(["soft", "hard", "overdrive"]); self._lo.addWidget(self.tp)
        self.dr = _slider_float(self._lo, "Drive", 0.5, 20, 3.0, 0.5, 1, "", 10)
        self._finish()
    def get_params(self): return {"type": self.tp.currentText(), "drive": self.dr.value()}
    def set_params(self, p):
        idx = self.tp.findText(p.get("type", "soft"))
        if idx >= 0: self.tp.setCurrentIndex(idx)
        self.dr.setValue(p.get("drive", 3.0))
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

def process(audio_data, start, end, sr=44100, **kw):
    result = audio_data.copy()
    sat_type = kw.get("type", "soft"); drive = kw.get("drive", 3.0)
    threshold = max(0.01, 1.0 / drive)
    if sat_type == "hard":
        result[start:end] = np.clip(result[start:end], -threshold, threshold) / threshold
    elif sat_type == "overdrive":
        seg = result[start:end].copy() * drive
        seg = np.where(seg >= 0, np.tanh(seg), np.tanh(seg * 0.8) * 1.2)
        result[start:end] = seg
    else:
        result[start:end] = np.tanh(result[start:end] * drive)
    return np.clip(result, -1.0, 1.0)
