# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "vinyl"
EFFECT_ICON    = "V"
EFFECT_COLOR   = "#606c38"
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
        super().__init__("Vinyl", p)
        self.a = _slider_float(self._lo, "Amount", 0, 1, 0.5, 0.1, 2)
        self._finish()
    def get_params(self): return {"amount": self.a.value()}
    def set_params(self, p): self.a.setValue(p.get("amount", 0.5))
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

from scipy.signal import butter, sosfilt

def process(audio_data, start, end, sr=44100, **kw):
    result = audio_data.copy(); segment = result[start:end].copy()
    if len(segment) == 0: return result
    amount = kw.get("amount", 0.5); rng = np.random.default_rng(); seg_len = len(segment)
    crackle = amount; noise = amount * 0.5; wow = amount * 0.3
    if crackle > 0:
        cs = np.zeros(seg_len, dtype=np.float32)
        n_pops = int(seg_len * crackle * 0.001)
        pp = rng.integers(0, seg_len, size=n_pops)
        cs[pp] = rng.uniform(0.02, 0.15, size=n_pops).astype(np.float32) * rng.choice([-1.0, 1.0], size=n_pops).astype(np.float32) * crackle
        nyq = sr / 2.0; sos = butter(2, min(1000.0 / nyq, 0.99), btype="high", output="sos")
        cs = sosfilt(sos, cs).astype(np.float32)
        if segment.ndim == 1: segment += cs
        else:
            for ch in range(segment.shape[1]): segment[:, ch] += cs
    if noise > 0:
        hiss = rng.normal(0, noise * 0.02, size=seg_len).astype(np.float32)
        nyq = sr / 2.0; sos = butter(2, min(3000.0 / nyq, 0.99), btype="high", output="sos")
        hiss = sosfilt(sos, hiss).astype(np.float32)
        if segment.ndim == 1: segment += hiss
        else:
            for ch in range(segment.shape[1]): segment[:, ch] += hiss
    if wow > 0:
        t = np.arange(seg_len, dtype=np.float32) / sr
        wow_sig = 1.0 + wow * 0.005 * np.sin(2 * np.pi * 1.5 * t)
        indices = np.cumsum(wow_sig).astype(np.float32)
        indices = np.clip(indices / indices[-1] * (seg_len - 1), 0, seg_len - 1).astype(int)
        segment = segment[indices]
    result[start:end] = np.clip(segment, -1.0, 1.0)
    return result
