# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "reverse"
EFFECT_ICON    = "R"
EFFECT_COLOR   = "#0f3460"
EFFECT_SECTION = "Basics"

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
        super().__init__("Reverse", p)
        self._lo.addWidget(QLabel("Reverses the selected audio."))
        self._finish()
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

def _apply_micro_fade(audio, fade_samples=64):
    result = audio.copy()
    n = min(fade_samples, len(result) // 2)
    if n == 0: return result
    fi = np.linspace(0, 1, n, dtype=np.float32)
    fo = np.linspace(1, 0, n, dtype=np.float32)
    if result.ndim == 1:
        result[:n] *= fi; result[-n:] *= fo
    else:
        for ch in range(result.shape[1]):
            result[:n, ch] *= fi; result[-n:, ch] *= fo
    return result

def process(audio_data, start, end, sr=44100, **kw):
    result = audio_data.copy()
    result[start:end] = result[start:end][::-1]
    fade = min(64, (end - start) // 4)
    if fade > 0:
        result[start:start+fade] = _apply_micro_fade(result[start:start+fade], fade)
    return result
