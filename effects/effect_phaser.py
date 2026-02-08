# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "phaser"
EFFECT_ICON    = "A"
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
        super().__init__("Phaser", p)
        self.rt = _slider_float(self._lo, "Rate (Hz)", 0.05, 10, 0.5, 0.1, 2, " Hz", 100)
        self.dp = _slider_float(self._lo, "Depth", 0, 1, 0.7, 0.1, 2)
        self.st = _slider_int(self._lo, "Stages", 1, 12, 4)
        self.mx = _slider_float(self._lo, "Mix", 0, 1, 0.7, 0.1, 2)
        self._finish()
    def get_params(self): return {"rate_hz": self.rt.value(), "depth": self.dp.value(), "stages": self.st.value(), "mix": self.mx.value()}
    def set_params(self, p):
        self.rt.setValue(p.get("rate_hz", 0.5)); self.dp.setValue(p.get("depth", 0.7))
        self.st.setValue(p.get("stages", 4)); self.mx.setValue(p.get("mix", 0.7))
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

from scipy.signal import lfilter

def process(audio_data, start, end, sr=44100, **kw):
    out = audio_data.copy(); seg = out[start:end].astype(np.float64)
    n = len(seg)
    if n == 0: return out
    rate_hz = kw.get("rate_hz", 0.5); depth = kw.get("depth", 0.7)
    stages = kw.get("stages", 4); mix = kw.get("mix", 0.7)
    if seg.ndim == 1: seg = seg.reshape(-1, 1)
    channels = seg.shape[1]; t_arr = np.arange(n, dtype=np.float64) / sr
    lfo = 100.0 + 3900.0 * depth * 0.5 * (1.0 + np.sin(2.0 * np.pi * rate_hz * t_arr))
    block_size = max(64, sr // 100); n_blocks = (n + block_size - 1) // block_size
    result = np.zeros_like(seg)
    for ch in range(channels):
        y = seg[:, ch].copy()
        for stage in range(stages):
            stage_offset = stage * 200.0; filtered = np.zeros(n); state = 0.0
            for blk in range(n_blocks):
                s = blk * block_size; e = min(s + block_size, n)
                center_freq = np.clip(lfo[s] + stage_offset, 20, sr / 2 - 100)
                omega = np.clip(np.pi * center_freq / sr, 0.001, np.pi * 0.49)
                a = (np.tan(omega) - 1.0) / (np.tan(omega) + 1.0)
                block_out, zf = lfilter(np.array([a, 1.0]), np.array([1.0, a]), y[s:e], zi=np.array([state]))
                filtered[s:e] = block_out; state = zf[0]
            y = filtered
        result[:, ch] = seg[:, ch] * (1.0 - mix) + y * mix
    out[start:end] = result.astype(np.float32)
    if out[start:end].ndim != audio_data[start:end].ndim:
        out[start:end] = result.squeeze().astype(np.float32)
    return out
