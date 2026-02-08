# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "chorus"
EFFECT_ICON    = "C"
EFFECT_COLOR   = "#2a6478"
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
        super().__init__("Chorus", p)
        self.dp = _slider_float(self._lo, "Depth (ms)", 0.5, 20, 5, 0.5, 1, " ms", 10)
        self.rt = _slider_float(self._lo, "Rate (Hz)", 0.1, 10, 1.5, 0.1, 1, " Hz", 10)
        self.vc = _slider_int(self._lo, "Voices", 1, 8, 2)
        self.mx = _slider_float(self._lo, "Mix", 0, 1, 0.5, 0.1, 2)
        self._finish()
    def get_params(self): return {"depth_ms": self.dp.value(), "rate_hz": self.rt.value(), "voices": self.vc.value(), "mix": self.mx.value()}
    def set_params(self, p):
        self.dp.setValue(p.get("depth_ms", 5)); self.rt.setValue(p.get("rate_hz", 1.5))
        self.vc.setValue(p.get("voices", 2)); self.mx.setValue(p.get("mix", 0.5))
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

def process(audio_data, start, end, sr=44100, **kw):
    out = audio_data.copy(); seg = out[start:end].astype(np.float64)
    n = len(seg); depth_samp = int(kw.get("depth_ms", 5.0) * sr / 1000.0)
    rate_hz = kw.get("rate_hz", 1.5); voices = kw.get("voices", 2); mix = kw.get("mix", 0.5)
    t_arr = np.arange(n, dtype=np.float64) / sr; result = seg.copy()
    for v in range(voices):
        phase = 2.0 * np.pi * v / max(voices, 1)
        delay_mod = (depth_samp * (1.0 + np.sin(2.0 * np.pi * rate_hz * t_arr + phase)) / 2.0).astype(int)
        indices = np.clip(np.arange(n) - delay_mod, 0, n - 1)
        if seg.ndim == 2:
            for ch in range(seg.shape[1]): result[:, ch] += seg[indices, ch]
        else: result += seg[indices]
    result = result / (1 + voices)
    out[start:end] = (seg * (1 - mix) + result * mix).astype(np.float32)
    return out
