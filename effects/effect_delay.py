# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "delay"
EFFECT_ICON    = "E"
EFFECT_COLOR   = "#2a9d8f"
EFFECT_SECTION = "Space & Texture"

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
        super().__init__("Delay", p)
        self.d = _slider_int(self._lo, "Delay (ms)", 10, 2000, 300, " ms")
        self.fb = _slider_float(self._lo, "Feedback", 0, 0.95, 0.4, 0.05, 2)
        self.mx = _slider_float(self._lo, "Mix", 0, 1, 0.5, 0.1, 2)
        self._finish()
    def get_params(self): return {"delay_ms": self.d.value(), "feedback": self.fb.value(), "mix": self.mx.value()}
    def set_params(self, p):
        self.d.setValue(int(p.get("delay_ms", 300))); self.fb.setValue(p.get("feedback", 0.4)); self.mx.setValue(p.get("mix", 0.5))
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

def process(audio_data, start, end, sr=44100, **kw):
    result = audio_data.copy(); segment = result[start:end].copy()
    if len(segment) == 0: return result
    delay_samples = max(1, int(kw.get("delay_ms", 200) * sr / 1000.0))
    feedback = max(0.0, min(0.95, kw.get("feedback", 0.6))); mix = kw.get("mix", 0.5)
    output = segment.copy()
    n_echoes = min(30, int(np.log(0.01) / np.log(max(feedback, 0.01))) + 1)
    for i in range(1, n_echoes + 1):
        offset = i * delay_samples
        if offset >= len(segment): break
        gain = feedback ** i
        if gain < 0.01: break
        echo_len = min(len(segment) - offset, len(segment))
        output[offset:offset + echo_len] += segment[:echo_len] * gain
    result[start:end] = segment * (1.0 - mix) + output * mix
    return np.clip(result, -1.0, 1.0)
