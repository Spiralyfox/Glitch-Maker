# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "tremolo"
EFFECT_ICON    = "~"
EFFECT_COLOR   = "#e07c24"
EFFECT_SECTION = "Modulation"

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
        super().__init__("Tremolo", p)
        self.rt = _slider_float(self._lo, "Rate (Hz)", 0.1, 30, 5, 0.5, 1, " Hz", 10)
        self.dp = _slider_float(self._lo, "Depth", 0, 1, 0.7, 0.1, 2)
        self._row("Shape"); self.sh = QComboBox(); self.sh.addItems(["sine", "square", "triangle", "saw"]); self._lo.addWidget(self.sh)
        self._finish()
    def get_params(self): return {"rate_hz": self.rt.value(), "depth": self.dp.value(), "shape": self.sh.currentText()}
    def set_params(self, p):
        self.rt.setValue(p.get("rate_hz", 5)); self.dp.setValue(p.get("depth", 0.7))
        idx = self.sh.findText(p.get("shape", "sine"))
        if idx >= 0: self.sh.setCurrentIndex(idx)
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

def process(audio_data, start, end, sr=44100, **kw):
    out = audio_data.copy(); seg = out[start:end].astype(np.float64); n = len(seg)
    rate_hz = kw.get("rate_hz", 5.0); depth = kw.get("depth", 0.7); shape = kw.get("shape", "sine")
    t_arr = np.arange(n, dtype=np.float64) / sr
    if shape == "sine": lfo = 0.5 * (1.0 + np.sin(2.0 * np.pi * rate_hz * t_arr))
    elif shape == "square": lfo = (np.sin(2.0 * np.pi * rate_hz * t_arr) >= 0).astype(np.float64)
    elif shape == "triangle": lfo = 2.0 * np.abs(2.0 * (rate_hz * t_arr - np.floor(rate_hz * t_arr + 0.5)))
    else: lfo = np.mod(rate_hz * t_arr, 1.0)
    envelope = 1.0 - depth * (1.0 - lfo)
    if seg.ndim == 2: envelope = envelope.reshape(-1, 1)
    out[start:end] = (seg * envelope).astype(np.float32)
    return out
