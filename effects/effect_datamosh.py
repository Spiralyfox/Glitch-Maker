# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "datamosh"
EFFECT_ICON    = "Z"
EFFECT_COLOR   = "#9b2226"
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
        super().__init__("Datamosh", p)
        self.bs = _slider_int(self._lo, "Block size", 64, 8192, 512)
        self.ch = _slider_float(self._lo, "Chaos", 0, 1, 0.5, 0.1, 2)
        self._finish()
    def get_params(self): return {"block_size": self.bs.value(), "chaos": self.ch.value()}
    def set_params(self, p): self.bs.setValue(p.get("block_size", 512)); self.ch.setValue(p.get("chaos", 0.5))
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

def process(audio_data, start, end, sr=44100, **kw):
    result = audio_data.copy(); segment = result[start:end].copy()
    if len(segment) == 0: return result
    block_size = kw.get("block_size", 512); intensity = kw.get("chaos", 0.5)
    rng = np.random.default_rng(); seg_len = len(segment)
    n_blocks = max(1, seg_len // block_size); n_affected = max(1, int(n_blocks * intensity))
    for _ in range(n_affected):
        i = rng.integers(0, n_blocks); j = rng.integers(0, n_blocks)
        s1 = i * block_size; e1 = min(s1 + block_size, seg_len)
        s2 = j * block_size; e2 = min(s2 + block_size, seg_len)
        bl = min(e1 - s1, e2 - s2)
        tmp = segment[s1:s1+bl].copy(); segment[s1:s1+bl] = segment[s2:s2+bl]; segment[s2:s2+bl] = tmp
    result[start:end] = np.clip(segment, -1.0, 1.0)
    return result
