# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "ring_mod"
EFFECT_ICON    = "M"
EFFECT_COLOR   = "#6d597a"
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
        super().__init__("Ring Mod", p)
        self.f = _slider_int(self._lo, "Frequency (Hz)", 1, 5000, 440, " Hz")
        self.mx = _slider_float(self._lo, "Mix", 0, 1, 0.5, 0.1, 2)
        self._finish()
    def get_params(self): return {"frequency": self.f.value(), "mix": self.mx.value()}
    def set_params(self, p): self.f.setValue(int(p.get("frequency", 440))); self.mx.setValue(p.get("mix", 0.5))
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

def process(audio_data, start, end, sr=44100, **kw):
    result = audio_data.copy(); segment = result[start:end].copy()
    if len(segment) == 0: return result
    freq = kw.get("frequency", 440); mix = kw.get("mix", 0.5)
    t = np.arange(len(segment), dtype=np.float32) / sr
    carrier = np.sin(2.0 * np.pi * freq * t).astype(np.float32)
    if segment.ndim == 1: modulated = segment * carrier
    else:
        modulated = segment.copy()
        for ch in range(segment.shape[1]): modulated[:, ch] = segment[:, ch] * carrier
    result[start:end] = segment * (1.0 - mix) + modulated * mix
    return np.clip(result, -1.0, 1.0)
