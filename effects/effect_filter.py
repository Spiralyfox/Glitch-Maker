# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "filter"
EFFECT_ICON    = "L"
EFFECT_COLOR   = "#264653"
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
        super().__init__("Filter", p)
        self._row("Type"); self.tp = QComboBox(); self.tp.addItems(["lowpass", "highpass", "bandpass"]); self._lo.addWidget(self.tp)
        self.cf = _slider_int(self._lo, "Cutoff (Hz)", 20, 20000, 1000, " Hz")
        self.rs = _slider_float(self._lo, "Resonance", 0.1, 20, 1.0, 0.5, 1, "", 10)
        self._finish()
    def get_params(self): return {"filter_type": self.tp.currentText(), "cutoff_hz": self.cf.value(), "resonance": self.rs.value()}
    def set_params(self, p):
        idx = self.tp.findText(p.get("filter_type", "lowpass"))
        if idx >= 0: self.tp.setCurrentIndex(idx)
        self.cf.setValue(int(p.get("cutoff_hz", 1000))); self.rs.setValue(p.get("resonance", 1.0))
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

from scipy.signal import butter, sosfilt

def _apply_filter(segment, ftype, cutoff, Q, sr):
    nyquist = sr / 2.0
    norm_cutoff = max(0.001, min(0.999, cutoff / nyquist))
    order = max(2, min(8, int(Q * 2)))
    btype = "low" if ftype == "lowpass" else "high"
    sos = butter(order, norm_cutoff, btype=btype, output="sos")
    if segment.ndim == 1:
        return sosfilt(sos, segment).astype(np.float32)
    out = segment.copy()
    for ch in range(segment.shape[1]):
        out[:, ch] = sosfilt(sos, segment[:, ch]).astype(np.float32)
    return out

def process(audio_data, start, end, sr=44100, **kw):
    result = audio_data.copy()
    seg = result[start:end].copy()
    if len(seg) == 0: return result
    nyquist = sr / 2.0
    cutoff = max(20.0, min(kw.get("cutoff_hz", 1000), nyquist * 0.95))
    result[start:end] = _apply_filter(seg, kw.get("filter_type", "lowpass"), cutoff, kw.get("resonance", 1.0), sr)
    return np.clip(result, -1.0, 1.0)
