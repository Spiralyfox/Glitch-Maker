# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "pan"
EFFECT_ICON    = "⊝"
EFFECT_COLOR   = "#2563eb"
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
        super().__init__("Pan / Stereo", p)
        self._lo.addWidget(QLabel("Turn the knob to pan L \u2194 R"))
        dial_row = QHBoxLayout(); dial_row.addStretch()
        lbl_l = QLabel("L"); lbl_l.setStyleSheet(f"color: {COLORS['text_dim']}; font-weight: bold; font-size: 14px;")
        lbl_l.setFixedWidth(20); dial_row.addWidget(lbl_l); dial_row.addSpacing(8)
        self.dial = QDial(); self.dial.setRange(-100, 100); self.dial.setValue(0)
        self.dial.setFixedSize(72, 72); self.dial.setNotchesVisible(True); self.dial.setWrapping(False)
        self.dial.setStyleSheet(f"QDial {{ background: {COLORS['bg_dark']}; border: 2px solid {COLORS['border']}; border-radius: 36px; }}")
        dial_row.addWidget(self.dial); dial_row.addSpacing(8)
        lbl_r = QLabel("R"); lbl_r.setStyleSheet(f"color: {COLORS['text_dim']}; font-weight: bold; font-size: 14px;")
        lbl_r.setFixedWidth(20); dial_row.addWidget(lbl_r); dial_row.addStretch()
        self._lo.addLayout(dial_row)
        self.pan_sb = _slider_float(self._lo, "Pan value (-1.0 L ... +1.0 R)", -1, 1, 0, 0.05, 2, "", 100)
        self.dial.valueChanged.connect(lambda v: self.pan_sb.setValue(v / 100))
        self.pan_sb.valueChanged.connect(lambda v: self.dial.setValue(int(v * 100)))
        self._lo.addSpacing(8)
        self.mono = QCheckBox("Convert to Mono (same on both sides)"); self._lo.addWidget(self.mono)
        self._finish()
    def get_params(self): return {"pan": self.pan_sb.value(), "mono": self.mono.isChecked()}
    def set_params(self, p):
        self.pan_sb.setValue(p.get("pan", 0)); self.dial.setValue(int(p.get("pan", 0) * 100))
        self.mono.setChecked(p.get("mono", False))
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

def process(audio_data, start, end, sr=44100, **kw):
    out = audio_data.copy()
    seg = out[start:end].astype(np.float64)
    if seg.ndim == 1: seg = np.column_stack([seg, seg])
    elif seg.shape[1] == 1: seg = np.column_stack([seg[:, 0], seg[:, 0]])
    if kw.get("mono", False):
        m = np.mean(seg[:, :2], axis=1); seg[:, 0] = m; seg[:, 1] = m
    pan_val = np.clip(kw.get("pan", 0.0), -1.0, 1.0)
    angle = (pan_val + 1.0) * np.pi / 4.0
    seg[:, 0] *= np.cos(angle); seg[:, 1] *= np.sin(angle)
    out[start:end] = seg.astype(np.float32)
    if out[start:end].ndim != audio_data[start:end].ndim:
        out[start:end] = seg[:, :audio_data.shape[1] if audio_data.ndim > 1 else 1].astype(np.float32)
    return out
