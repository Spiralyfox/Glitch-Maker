# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "buffer_freeze"
EFFECT_ICON    = "F"
EFFECT_COLOR   = "#457b9d"
EFFECT_SECTION = "Glitch"

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
        super().__init__("Buffer Freeze", p)
        self.bs = _slider_int(self._lo, "Buffer size (ms)", 10, 500, 50, " ms")
        self._finish()
    def get_params(self): return {"buffer_ms": self.bs.value()}
    def set_params(self, p): self.bs.setValue(p.get("buffer_ms", 50))
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

def process(audio_data, start, end, sr=44100, **kw):
    result = audio_data.copy(); segment = result[start:end]
    if len(segment) == 0: return result
    grain_len = max(64, min(int(kw.get("buffer_ms", 50) * sr / 1000.0), len(segment)))
    grain = segment[:grain_len].copy()
    n = min(32, grain_len // 4)
    if n > 0:
        fi = np.linspace(0, 1, n, dtype=np.float32); fo = np.linspace(1, 0, n, dtype=np.float32)
        if grain.ndim == 1: grain[:n] *= fi; grain[-n:] *= fo
        else:
            for ch in range(grain.shape[1]): grain[:n, ch] *= fi; grain[-n:, ch] *= fo
    target_len = end - start; n_reps = max(1, target_len // grain_len + 1)
    frozen = np.concatenate([grain] * n_reps, axis=0)
    if len(frozen) > target_len: frozen = frozen[:target_len]
    elif len(frozen) < target_len:
        frozen = np.concatenate([frozen, np.zeros((target_len - len(frozen),) + frozen.shape[1:], dtype=np.float32)], axis=0)
    result[start:end] = frozen
    return result
