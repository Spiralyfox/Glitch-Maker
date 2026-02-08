# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "bitcrusher"
EFFECT_ICON    = "B"
EFFECT_COLOR   = "#533483"
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
        super().__init__("Bitcrusher", p)
        self.bd = _slider_int(self._lo, "Bit Depth", 1, 16, 8)
        self.ds = _slider_int(self._lo, "Downsample", 1, 64, 1)
        self._finish()
    def get_params(self): return {"bit_depth": self.bd.value(), "downsample": self.ds.value()}
    def set_params(self, p): self.bd.setValue(p.get("bit_depth", 8)); self.ds.setValue(p.get("downsample", 1))
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

def process(audio_data, start, end, sr=44100, **kw):
    result = audio_data.copy(); segment = result[start:end].copy()
    if len(segment) == 0: return result
    bd = max(1, min(16, kw.get("bit_depth", 8))); levels = 2 ** bd
    segment = np.round(segment * levels) / levels
    ds = max(1, min(64, kw.get("downsample", 1)))
    if ds > 1:
        if segment.ndim == 1:
            held = np.repeat(segment[::ds], ds); segment = held[:len(result[start:end])]
        else:
            for ch in range(segment.shape[1]):
                held = np.repeat(segment[::ds, ch], ds); segment[:len(held), ch] = held[:len(segment)]
    result[start:end] = segment[:len(result[start:end])]
    return result
