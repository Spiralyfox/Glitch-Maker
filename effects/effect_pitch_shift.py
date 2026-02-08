# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "pitch_shift"
EFFECT_ICON    = "P"
EFFECT_COLOR   = "#16c79a"
EFFECT_SECTION = "Pitch & Time"

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
        super().__init__("Pitch Shift", p)
        self.st = _slider_float(self._lo, "Semitones", -24, 24, 0, 1, 1, " st", 10)
        self.simple = QCheckBox("Simple mode (faster)"); self._lo.addWidget(self.simple)
        self._finish()
    def get_params(self): return {"semitones": self.st.value(), "simple": self.simple.isChecked()}
    def set_params(self, p): self.st.setValue(p.get("semitones", 0)); self.simple.setChecked(p.get("simple", False))
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

from scipy.signal import resample as scipy_resample

def _micro_fade(audio, n=64):
    result = audio.copy(); n = min(n, len(result) // 2)
    if n == 0: return result
    fi = np.linspace(0, 1, n, dtype=np.float32); fo = np.linspace(1, 0, n, dtype=np.float32)
    if result.ndim == 1: result[:n] *= fi; result[-n:] *= fo
    else:
        for ch in range(result.shape[1]): result[:n, ch] *= fi; result[-n:, ch] *= fo
    return result

def process(audio_data, start, end, sr=44100, **kw):
    semitones = kw.get("semitones", 0)
    factor = 2.0 ** (semitones / 12.0)
    segment = audio_data[start:end].copy()
    if len(segment) == 0: return audio_data.copy()
    original_len = len(segment)
    new_len = int(original_len / factor)
    if new_len < 2: return audio_data.copy()
    if kw.get("simple", False):
        before = audio_data[:start].copy(); after = audio_data[end:].copy()
        if segment.ndim == 1: shifted = scipy_resample(segment, new_len)
        else:
            channels = [scipy_resample(segment[:, ch], new_len) for ch in range(segment.shape[1])]
            shifted = np.column_stack(channels)
        shifted = _micro_fade(shifted.astype(np.float32), 64)
        return np.concatenate([before, shifted, after], axis=0)
    result = audio_data.copy()
    if segment.ndim == 1:
        shifted = scipy_resample(scipy_resample(segment, new_len), original_len)
    else:
        channels = [scipy_resample(scipy_resample(segment[:, ch], new_len), original_len) for ch in range(segment.shape[1])]
        shifted = np.column_stack(channels)
    result[start:end] = _micro_fade(shifted.astype(np.float32), 64)[:len(result[start:end])]
    return np.clip(result, -1.0, 1.0)
