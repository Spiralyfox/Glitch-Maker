# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "shuffle"
EFFECT_ICON    = "K"
EFFECT_COLOR   = "#bb3e03"
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
        super().__init__("Shuffle", p)
        self.n = _slider_int(self._lo, "Number of slices", 2, 64, 8)
        self._finish()
    def get_params(self): return {"num_slices": self.n.value()}
    def set_params(self, p): self.n.setValue(p.get("num_slices", 8))
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

def process(audio_data, start, end, sr=44100, **kw):
    result = audio_data.copy(); segment = result[start:end].copy()
    if len(segment) == 0: return result
    slices = kw.get("num_slices", 8); seg_len = len(segment)
    slice_len = max(64, seg_len // slices); rng = np.random.default_rng()
    chunks = []
    for i in range(slices):
        s = i * slice_len; e = min(s + slice_len, seg_len)
        if s >= seg_len: break
        chunk = segment[s:e].copy()
        n = min(16, len(chunk) // 4)
        if n > 0:
            fi = np.linspace(0, 1, n, dtype=np.float32); fo = np.linspace(1, 0, n, dtype=np.float32)
            if chunk.ndim == 1: chunk[:n] *= fi; chunk[-n:] *= fo
            else:
                for ch in range(chunk.shape[1]): chunk[:n, ch] *= fi; chunk[-n:, ch] *= fo
        chunks.append(chunk)
    if not chunks: return result
    rng.shuffle(chunks)
    output = np.concatenate(chunks, axis=0)
    target_len = end - start
    if len(output) > target_len: output = output[:target_len]
    elif len(output) < target_len:
        output = np.concatenate([output, np.zeros((target_len - len(output),) + output.shape[1:], dtype=np.float32)], axis=0)
    result[start:end] = output
    return result
