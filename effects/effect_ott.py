# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "ott"
EFFECT_ICON    = "O"
EFFECT_COLOR   = "#e76f51"
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
        super().__init__("OTT", p)
        self.d = _slider_float(self._lo, "Depth", 0, 1, 0.5, 0.1, 2)
        self._finish()
    def get_params(self): return {"depth": self.d.value()}
    def set_params(self, p): self.d.setValue(p.get("depth", 0.5))
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

from scipy.signal import butter, sosfilt

def _band(audio, low_freq, high_freq, sr):
    nyquist = sr / 2.0; low_n = max(0.001, low_freq / nyquist); high_n = min(0.999, high_freq / nyquist)
    if low_n <= 0.001: sos = butter(4, high_n, btype="low", output="sos")
    elif high_n >= 0.999: sos = butter(4, low_n, btype="high", output="sos")
    else: sos = butter(4, [low_n, high_n], btype="band", output="sos")
    return sosfilt(sos, audio).astype(np.float32)

def _compress(audio, threshold=0.1, ratio=8.0, depth=1.0):
    output = audio.copy(); abs_s = np.abs(output); mask = abs_s > threshold
    if np.any(mask):
        excess = abs_s[mask] - threshold; target = threshold + excess / ratio
        gain = np.ones_like(abs_s); gain[mask] = target / (abs_s[mask] + 1e-10)
        gain = 1.0 + (gain - 1.0) * depth; output *= gain
    output *= (1.0 + depth * 2.0)
    return np.clip(output, -1.0, 1.0).astype(np.float32)

def process(audio_data, start, end, sr=44100, **kw):
    result = audio_data.copy(); segment = result[start:end].copy()
    if len(segment) == 0: return result
    depth = max(0.0, min(1.0, kw.get("depth", 0.5)))
    is_stereo = segment.ndim > 1 and segment.shape[1] >= 2
    mono = np.mean(segment, axis=1) if is_stereo else segment.copy()
    nyquist = sr / 2.0
    low = _band(mono, 0, 200, sr); mid = _band(mono, 200, 5000, sr); high = _band(mono, 5000, nyquist * 0.95, sr)
    combined = _compress(low, 0.1, 8.0, depth) + _compress(mid, 0.08, 10.0, depth) + _compress(high, 0.05, 12.0, depth)
    combined = np.clip(combined, -1.0, 1.0).astype(np.float32)
    if is_stereo: result[start:end, 0] = combined; result[start:end, 1] = combined
    else: result[start:end] = combined
    return result
