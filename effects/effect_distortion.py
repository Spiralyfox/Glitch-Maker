# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "distortion"
EFFECT_ICON    = "W"
EFFECT_COLOR   = "#b5179e"
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
        super().__init__("Distortion", p)
        self.dr = _slider_float(self._lo, "Drive", 1, 20, 5, 0.5, 1, "", 10)
        self.tn = _slider_float(self._lo, "Tone", 0, 1, 0.5, 0.1, 2)
        self._row("Mode"); self.md = QComboBox(); self.md.addItems(["tube", "fuzz", "digital", "scream"]); self._lo.addWidget(self.md)
        self._finish()
    def get_params(self): return {"drive": self.dr.value(), "tone": self.tn.value(), "mode": self.md.currentText()}
    def set_params(self, p):
        self.dr.setValue(p.get("drive", 5.0)); self.tn.setValue(p.get("tone", 0.5))
        idx = self.md.findText(p.get("mode", "tube"))
        if idx >= 0: self.md.setCurrentIndex(idx)
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

def process(audio_data, start, end, sr=44100, **kw):
    out = audio_data.copy()
    drive = kw.get("drive", 5.0); tone = kw.get("tone", 0.5); mode = kw.get("mode", "tube")
    seg = out[start:end].astype(np.float64) * drive
    if mode == "tube": seg = np.sign(seg) * (1.0 - np.exp(-np.abs(seg)))
    elif mode == "fuzz": seg = np.tanh(seg * 2.0) * np.sign(seg + 0.001)
    elif mode == "digital":
        seg = np.clip(seg, -1.0, 1.0); steps = max(2, int(16 / drive)); seg = np.round(seg * steps) / steps
    elif mode == "scream": seg = np.tanh(seg * 3.0); seg = np.sign(seg) * np.power(np.abs(seg), 0.3)
    if tone < 0.95:
        alpha = tone * 0.99
        for i in range(1, len(seg)):
            if seg.ndim == 2: seg[i] = alpha * seg[i-1] + (1 - alpha) * seg[i]
            else: seg[i] = alpha * seg[i-1] + (1 - alpha) * seg[i]
    out[start:end] = np.clip(seg, -1.0, 1.0).astype(np.float32)
    return out
