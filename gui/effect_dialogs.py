"""Effect parameter dialogs for all 21 effects."""
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel,
    QSlider, QSpinBox, QDoubleSpinBox, QComboBox,
    QPushButton, QCheckBox, QLineEdit
)
from PyQt6.QtCore import Qt
from utils.config import COLORS

_SS = f"""
QDialog {{ background: {COLORS['bg_medium']}; }}
QLabel {{ color: {COLORS['text']}; font-size: 11px; }}
QSlider::groove:horizontal {{ background: {COLORS['bg_dark']}; height: 5px; border-radius: 2px; }}
QSlider::handle:horizontal {{ background: {COLORS['accent']}; width: 12px; height: 12px; margin: -4px 0; border-radius: 6px; }}
QSlider::sub-page:horizontal {{ background: {COLORS['accent_secondary']}; border-radius: 2px; }}
QSpinBox, QDoubleSpinBox, QComboBox, QLineEdit {{ background: {COLORS['bg_dark']}; color: {COLORS['text']};
    border: 1px solid {COLORS['border']}; border-radius: 4px; padding: 4px; font-size: 11px; }}
QCheckBox {{ color: {COLORS['text']}; font-size: 11px; }}
"""

def _btn(text, bg=COLORS['accent']):
    b = QPushButton(text); b.setFixedHeight(30)
    b.setCursor(Qt.CursorShape.PointingHandCursor)
    b.setStyleSheet(f"QPushButton {{ background: {bg}; color: white; border: none; border-radius: 5px; font-weight: bold; }} QPushButton:hover {{ background: {COLORS['accent_hover']}; }}")
    return b

class _Base(QDialog):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title); self.setFixedWidth(340); self.setStyleSheet(_SS)
        self._lo = QVBoxLayout(self); self._lo.setSpacing(8); self._lo.setContentsMargins(16, 12, 16, 12)
        t = QLabel(title); t.setStyleSheet(f"color: {COLORS['accent']}; font-size: 14px; font-weight: bold;"); self._lo.addWidget(t)
    def _row(self, label): self._lo.addWidget(QLabel(label))
    def _finish(self):
        r = QHBoxLayout()
        bc = _btn("Cancel", COLORS['button_bg']); bc.clicked.connect(self.reject); r.addWidget(bc)
        ba = _btn("Apply"); ba.clicked.connect(self.accept); r.addWidget(ba)
        self._lo.addLayout(r)
    def get_params(self) -> dict: return {}

class StutterDialog(_Base):
    def __init__(self, p=None):
        super().__init__("Stutter", p)
        self._row("Repeats"); self.rep = QSpinBox(); self.rep.setRange(1, 64); self.rep.setValue(4); self._lo.addWidget(self.rep)
        self._row("Chunk size (ms)"); self.sz = QSpinBox(); self.sz.setRange(5, 500); self.sz.setValue(80); self._lo.addWidget(self.sz)
        self._finish()
    def get_params(self): return {"repeats": self.rep.value(), "size_ms": self.sz.value()}

class BitcrusherDialog(_Base):
    def __init__(self, p=None):
        super().__init__("Bitcrusher", p)
        self._row("Bit depth"); self.bd = QSpinBox(); self.bd.setRange(1, 24); self.bd.setValue(8); self._lo.addWidget(self.bd)
        self._row("Downsample factor"); self.ds = QSpinBox(); self.ds.setRange(1, 32); self.ds.setValue(1); self._lo.addWidget(self.ds)
        self._finish()
    def get_params(self): return {"bit_depth": self.bd.value(), "downsample": self.ds.value()}

class SaturationDialog(_Base):
    def __init__(self, p=None):
        super().__init__("Saturation", p)
        self._row("Type"); self.tp = QComboBox(); self.tp.addItems(["hard", "soft", "overdrive"]); self._lo.addWidget(self.tp)
        self._row("Drive"); self.dr = QDoubleSpinBox(); self.dr.setRange(1, 20); self.dr.setValue(3); self.dr.setSingleStep(0.5); self._lo.addWidget(self.dr)
        self._finish()
    def get_params(self): return {"type": self.tp.currentText(), "drive": self.dr.value()}

class ReverseDialog(_Base):
    def __init__(self, p=None):
        super().__init__("Reverse", p); self._lo.addWidget(QLabel("Reverses the selected audio.")); self._finish()
    def get_params(self): return {}

class PitchShiftDialog(_Base):
    def __init__(self, p=None):
        super().__init__("Pitch Shift", p)
        self._row("Semitones"); self.st = QDoubleSpinBox(); self.st.setRange(-24, 24); self.st.setValue(0); self.st.setSingleStep(1); self._lo.addWidget(self.st)
        self.simple = QCheckBox("Simple mode (faster)"); self._lo.addWidget(self.simple)
        self._finish()
    def get_params(self): return {"semitones": self.st.value(), "simple": self.simple.isChecked()}

class TimeStretchDialog(_Base):
    def __init__(self, p=None):
        super().__init__("Time Stretch", p)
        self._row("Factor (0.25=4x faster, 4.0=4x slower)"); self.f = QDoubleSpinBox(); self.f.setRange(0.1, 8); self.f.setValue(1); self.f.setSingleStep(0.1); self._lo.addWidget(self.f)
        self._finish()
    def get_params(self): return {"factor": self.f.value()}

class GranularDialog(_Base):
    def __init__(self, p=None):
        super().__init__("Granular", p)
        self._row("Grain size (ms)"); self.gs = QSpinBox(); self.gs.setRange(5, 500); self.gs.setValue(50); self._lo.addWidget(self.gs)
        self._row("Density"); self.dn = QSpinBox(); self.dn.setRange(1, 16); self.dn.setValue(4); self._lo.addWidget(self.dn)
        self._row("Chaos (0-1)"); self.ch = QDoubleSpinBox(); self.ch.setRange(0, 1); self.ch.setValue(0.5); self.ch.setSingleStep(0.1); self._lo.addWidget(self.ch)
        self._finish()
    def get_params(self): return {"grain_ms": self.gs.value(), "density": self.dn.value(), "chaos": self.ch.value()}

class TapeStopDialog(_Base):
    def __init__(self, p=None):
        super().__init__("Tape Stop", p)
        self._row("Duration (ms)"); self.d = QSpinBox(); self.d.setRange(100, 5000); self.d.setValue(1500); self.d.setSingleStep(100); self._lo.addWidget(self.d)
        self._finish()
    def get_params(self): return {"duration_ms": self.d.value()}

class BufferFreezeDialog(_Base):
    def __init__(self, p=None):
        super().__init__("Buffer Freeze", p)
        self._row("Buffer size (ms)"); self.bs = QSpinBox(); self.bs.setRange(10, 500); self.bs.setValue(50); self._lo.addWidget(self.bs)
        self._finish()
    def get_params(self): return {"buffer_ms": self.bs.value()}

class DelayDialog(_Base):
    def __init__(self, p=None):
        super().__init__("Delay", p)
        self._row("Delay (ms)"); self.d = QSpinBox(); self.d.setRange(10, 2000); self.d.setValue(300); self._lo.addWidget(self.d)
        self._row("Feedback (0-1)"); self.fb = QDoubleSpinBox(); self.fb.setRange(0, 0.95); self.fb.setValue(0.4); self.fb.setSingleStep(0.05); self._lo.addWidget(self.fb)
        self._row("Mix"); self.mx = QDoubleSpinBox(); self.mx.setRange(0, 1); self.mx.setValue(0.5); self.mx.setSingleStep(0.1); self._lo.addWidget(self.mx)
        self._finish()
    def get_params(self): return {"delay_ms": self.d.value(), "feedback": self.fb.value(), "mix": self.mx.value()}

class RingModDialog(_Base):
    def __init__(self, p=None):
        super().__init__("Ring Mod", p)
        self._row("Frequency (Hz)"); self.f = QSpinBox(); self.f.setRange(1, 5000); self.f.setValue(440); self._lo.addWidget(self.f)
        self._row("Mix"); self.mx = QDoubleSpinBox(); self.mx.setRange(0, 1); self.mx.setValue(0.5); self.mx.setSingleStep(0.1); self._lo.addWidget(self.mx)
        self._finish()
    def get_params(self): return {"frequency": self.f.value(), "mix": self.mx.value()}

class FilterDialog(_Base):
    def __init__(self, p=None):
        super().__init__("Filter", p)
        self._row("Type"); self.tp = QComboBox(); self.tp.addItems(["lowpass", "highpass", "bandpass"]); self._lo.addWidget(self.tp)
        self._row("Cutoff (Hz)"); self.cf = QSpinBox(); self.cf.setRange(20, 20000); self.cf.setValue(1000); self.cf.setSingleStep(100); self._lo.addWidget(self.cf)
        self._row("Resonance"); self.rs = QDoubleSpinBox(); self.rs.setRange(0.1, 20); self.rs.setValue(1); self.rs.setSingleStep(0.5); self._lo.addWidget(self.rs)
        self._finish()
    def get_params(self): return {"filter_type": self.tp.currentText(), "cutoff_hz": self.cf.value(), "resonance": self.rs.value()}

class OTTDialog(_Base):
    def __init__(self, p=None):
        super().__init__("OTT", p)
        self._row("Depth (0-1)"); self.d = QDoubleSpinBox(); self.d.setRange(0, 1); self.d.setValue(0.5); self.d.setSingleStep(0.1); self._lo.addWidget(self.d)
        self._finish()
    def get_params(self): return {"depth": self.d.value()}

class VinylDialog(_Base):
    def __init__(self, p=None):
        super().__init__("Vinyl", p)
        self._row("Amount (0-1)"); self.a = QDoubleSpinBox(); self.a.setRange(0, 1); self.a.setValue(0.5); self.a.setSingleStep(0.1); self._lo.addWidget(self.a)
        self._finish()
    def get_params(self): return {"amount": self.a.value()}

class DatamoshDialog(_Base):
    def __init__(self, p=None):
        super().__init__("Datamosh", p)
        self._row("Block size"); self.bs = QSpinBox(); self.bs.setRange(64, 8192); self.bs.setValue(512); self.bs.setSingleStep(64); self._lo.addWidget(self.bs)
        self._row("Chaos (0-1)"); self.ch = QDoubleSpinBox(); self.ch.setRange(0, 1); self.ch.setValue(0.5); self.ch.setSingleStep(0.1); self._lo.addWidget(self.ch)
        self._finish()
    def get_params(self): return {"block_size": self.bs.value(), "chaos": self.ch.value()}

class ShuffleDialog(_Base):
    def __init__(self, p=None):
        super().__init__("Shuffle", p)
        self._row("Number of slices"); self.n = QSpinBox(); self.n.setRange(2, 64); self.n.setValue(8); self._lo.addWidget(self.n)
        self._finish()
    def get_params(self): return {"num_slices": self.n.value()}

class VolumeDialog(_Base):
    def __init__(self, p=None):
        super().__init__("Volume", p)
        self._row("Gain (%)")
        row = QHBoxLayout()
        self.sl = QSlider(Qt.Orientation.Horizontal); self.sl.setRange(0, 10000); self.sl.setValue(100)
        self.inp = QSpinBox(); self.inp.setRange(0, 10000); self.inp.setValue(100); self.inp.setSuffix(" %")
        self.sl.valueChanged.connect(self.inp.setValue); self.inp.valueChanged.connect(self.sl.setValue)
        row.addWidget(self.sl, stretch=1); row.addWidget(self.inp)
        self._lo.addLayout(row)
        self._finish()
    def get_params(self): return {"gain_pct": self.inp.value()}

class ChorusDialog(_Base):
    def __init__(self, p=None):
        super().__init__("Chorus", p)
        self._row("Depth (ms)"); self.dp = QDoubleSpinBox(); self.dp.setRange(0.5, 30); self.dp.setValue(5); self.dp.setSingleStep(0.5); self._lo.addWidget(self.dp)
        self._row("Rate (Hz)"); self.rt = QDoubleSpinBox(); self.rt.setRange(0.1, 10); self.rt.setValue(1.5); self.rt.setSingleStep(0.1); self._lo.addWidget(self.rt)
        self._row("Voices"); self.vc = QSpinBox(); self.vc.setRange(1, 8); self.vc.setValue(2); self._lo.addWidget(self.vc)
        self._row("Mix"); self.mx = QDoubleSpinBox(); self.mx.setRange(0, 1); self.mx.setValue(0.5); self.mx.setSingleStep(0.1); self._lo.addWidget(self.mx)
        self._finish()
    def get_params(self): return {"depth_ms": self.dp.value(), "rate_hz": self.rt.value(), "voices": self.vc.value(), "mix": self.mx.value()}

class DistortionDialog(_Base):
    def __init__(self, p=None):
        super().__init__("Distortion", p)
        self._row("Mode"); self.md = QComboBox(); self.md.addItems(["tube", "fuzz", "digital", "scream"]); self._lo.addWidget(self.md)
        self._row("Drive"); self.dr = QDoubleSpinBox(); self.dr.setRange(1, 20); self.dr.setValue(5); self.dr.setSingleStep(0.5); self._lo.addWidget(self.dr)
        self._row("Tone"); self.tn = QDoubleSpinBox(); self.tn.setRange(0, 1); self.tn.setValue(0.5); self.tn.setSingleStep(0.05); self._lo.addWidget(self.tn)
        self._finish()
    def get_params(self): return {"drive": self.dr.value(), "tone": self.tn.value(), "mode": self.md.currentText()}

class PhaserDialog(_Base):
    def __init__(self, p=None):
        super().__init__("Phaser", p)
        self._row("Rate (Hz)"); self.rt = QDoubleSpinBox(); self.rt.setRange(0.05, 10); self.rt.setValue(0.5); self.rt.setSingleStep(0.1); self._lo.addWidget(self.rt)
        self._row("Depth"); self.dp = QDoubleSpinBox(); self.dp.setRange(0, 1); self.dp.setValue(0.7); self.dp.setSingleStep(0.1); self._lo.addWidget(self.dp)
        self._row("Stages"); self.st = QSpinBox(); self.st.setRange(1, 12); self.st.setValue(4); self._lo.addWidget(self.st)
        self._row("Mix"); self.mx = QDoubleSpinBox(); self.mx.setRange(0, 1); self.mx.setValue(0.7); self.mx.setSingleStep(0.1); self._lo.addWidget(self.mx)
        self._finish()
    def get_params(self): return {"rate_hz": self.rt.value(), "depth": self.dp.value(), "stages": self.st.value(), "mix": self.mx.value()}

class TremoloDialog(_Base):
    def __init__(self, p=None):
        super().__init__("Tremolo", p)
        self._row("Rate (Hz)"); self.rt = QDoubleSpinBox(); self.rt.setRange(0.1, 30); self.rt.setValue(5); self.rt.setSingleStep(0.5); self._lo.addWidget(self.rt)
        self._row("Depth"); self.dp = QDoubleSpinBox(); self.dp.setRange(0, 1); self.dp.setValue(0.7); self.dp.setSingleStep(0.1); self._lo.addWidget(self.dp)
        self._row("Shape"); self.sh = QComboBox(); self.sh.addItems(["sine", "square", "triangle", "saw"]); self._lo.addWidget(self.sh)
        self._finish()
    def get_params(self): return {"rate_hz": self.rt.value(), "depth": self.dp.value(), "shape": self.sh.currentText()}
