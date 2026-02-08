# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "stutter"
EFFECT_ICON    = "S"
EFFECT_COLOR   = "#e94560"
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
        super().__init__("Stutter", p)
        self.rep = _slider_int(self._lo, "Repeats", 1, 64, 4)
        self.dec = _slider_float(self._lo, "Decay", 0, 1, 0.0, 0.1, 2)
        self._row("Mode"); self.md = QComboBox(); self.md.addItems(["normal", "halving", "reverse_alt"]); self._lo.addWidget(self.md)
        self._finish()
    def get_params(self): return {"repeats": self.rep.value(), "decay": self.dec.value(), "stutter_mode": self.md.currentText()}
    def set_params(self, p):
        self.rep.setValue(p.get("repeats", 4)); self.dec.setValue(p.get("decay", 0.0))
        idx = self.md.findText(p.get("stutter_mode", "normal"))
        if idx >= 0: self.md.setCurrentIndex(idx)
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

def _mf(audio, n=64):
    result = audio.copy(); n = min(n, len(result) // 2)
    if n == 0: return result
    fi = np.linspace(0, 1, n, dtype=np.float32); fo = np.linspace(1, 0, n, dtype=np.float32)
    if result.ndim == 1: result[:n] *= fi; result[-n:] *= fo
    else:
        for ch in range(result.shape[1]): result[:n, ch] *= fi; result[-n:, ch] *= fo
    return result

def process(audio_data, start, end, sr=44100, **kw):
    segment = audio_data[start:end].copy()
    if len(segment) == 0: return audio_data.copy()
    repeats = kw.get("repeats", 4); decay = kw.get("decay", 0.0); mode = kw.get("stutter_mode", "normal")
    segment = _mf(segment, min(64, len(segment) // 4))
    parts = []
    for i in range(repeats):
        if mode == "halving": part = segment[:max(64, len(segment) // (2 ** i))].copy()
        elif mode == "reverse_alt": part = segment[::-1].copy() if i % 2 else segment.copy()
        else: part = segment.copy()
        if decay > 0: part = part * ((1.0 - decay) ** i)
        parts.append(_mf(part, min(32, len(part) // 4)))
    before = audio_data[:start]; after = audio_data[end:]
    return np.concatenate([before, np.concatenate(parts, axis=0), after], axis=0)
