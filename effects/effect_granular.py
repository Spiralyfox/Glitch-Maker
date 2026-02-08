# ══════════════════════════════════════════════════
# Effect Metadata (edit these to customize)
# ══════════════════════════════════════════════════
EFFECT_ID      = "granular"
EFFECT_ICON    = "G"
EFFECT_COLOR   = "#7b2d8e"
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
        super().__init__("Granular", p)
        self.gs = _slider_int(self._lo, "Grain size (ms)", 5, 500, 50, " ms")
        self.dn = _slider_int(self._lo, "Density", 1, 16, 4)
        self.ch = _slider_float(self._lo, "Chaos", 0, 1, 0.5, 0.1, 2)
        self._finish()
    def get_params(self): return {"grain_ms": self.gs.value(), "density": self.dn.value(), "chaos": self.ch.value()}
    def set_params(self, p):
        self.gs.setValue(p.get("grain_ms", 50)); self.dn.setValue(p.get("density", 4)); self.ch.setValue(p.get("chaos", 0.5))
# ══════════════════════════════════════════════════
# DSP / Process
# ══════════════════════════════════════════════════

def _mf(audio, n=32):
    result = audio.copy(); n = min(n, len(result) // 2)
    if n == 0: return result
    fi = np.linspace(0, 1, n, dtype=np.float32); fo = np.linspace(1, 0, n, dtype=np.float32)
    if result.ndim == 1: result[:n] *= fi; result[-n:] *= fo
    else:
        for ch in range(result.shape[1]): result[:n, ch] *= fi; result[-n:, ch] *= fo
    return result

def process(audio_data, start, end, sr=44100, **kw):
    result = audio_data.copy(); segment = result[start:end].copy()
    if len(segment) == 0: return result
    grain_samples = max(64, int(kw.get("grain_ms", 50) * sr / 1000.0))
    density = kw.get("density", 4); randomize = kw.get("chaos", 0.5)
    n_grains = max(1, len(segment) // grain_samples)
    grains = [_mf(segment[i*grain_samples:min((i+1)*grain_samples, len(segment))].copy()) for i in range(n_grains)]
    if not grains: return result
    rng = np.random.default_rng(); indices = np.arange(len(grains))
    if randomize > 0:
        for _ in range(int(len(grains) * randomize)):
            i, j = rng.integers(0, len(grains), size=2); indices[i], indices[j] = indices[j], indices[i]
    out_grains = []
    for idx in indices:
        out_grains.append(grains[idx])
        if density > 1.0 and rng.random() < (density - 1.0): out_grains.append(grains[idx])
    output = np.concatenate(out_grains, axis=0)
    target_len = end - start
    if len(output) > target_len: output = output[:target_len]
    elif len(output) < target_len:
        output = np.concatenate([output, np.zeros((target_len - len(output),) + output.shape[1:], dtype=np.float32)], axis=0)
    result[start:end] = output
    return result
