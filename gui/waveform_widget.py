"""Waveform display with selection + clip highlight."""
import numpy as np
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QImage, QFont
from utils.config import COLORS
from utils.translator import t

class WaveformWidget(QWidget):
    position_clicked = pyqtSignal(int)
    selection_changed = pyqtSignal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_data: np.ndarray | None = None
        self.sample_rate = 44100
        self.selection_start: int | None = None
        self.selection_end: int | None = None
        self._clip_hl_start: int | None = None
        self._clip_hl_end: int | None = None
        self._playhead: int = 0
        self._dragging = False
        self._cache: QImage | None = None
        self._cache_w = 0
        self.setMinimumHeight(120)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def set_audio(self, data, sr):
        self.audio_data = data; self.sample_rate = sr
        self._cache = None; self.update()

    def set_playhead(self, pos):
        self._playhead = pos; self.update()

    def set_selection(self, s, e):
        self.selection_start, self.selection_end = s, e; self.update()

    def set_clip_highlight(self, s, e):
        self._clip_hl_start, self._clip_hl_end = s, e; self.update()

    def _pos_to_sample(self, x):
        if self.audio_data is None: return 0
        return int(max(0, min(x / self.width(), 1.0)) * len(self.audio_data))

    def _sample_to_x(self, s):
        if self.audio_data is None or len(self.audio_data) == 0: return 0
        return int(s / len(self.audio_data) * self.width())

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.audio_data is not None:
            self._dragging = True
            self.selection_start = self._pos_to_sample(e.position().x())
            self.selection_end = self.selection_start
            # Clear clip highlight when starting a new waveform selection
            self._clip_hl_start = None
            self._clip_hl_end = None
            self.update()

    def mouseMoveEvent(self, e):
        if self._dragging and self.audio_data is not None:
            self.selection_end = self._pos_to_sample(e.position().x()); self.update()

    def mouseReleaseEvent(self, e):
        if self._dragging:
            self._dragging = False
            if self.selection_start is not None and self.selection_end is not None:
                if abs(self.selection_end - self.selection_start) < 100:
                    self.position_clicked.emit(self._pos_to_sample(e.position().x()))
                    self.selection_start = self.selection_end = None
                else:
                    s, en = min(self.selection_start, self.selection_end), max(self.selection_start, self.selection_end)
                    self.selection_start, self.selection_end = s, en
                    self.selection_changed.emit(s, en)
            self.update()

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor(COLORS['bg_dark']))

        if self.audio_data is None or len(self.audio_data) == 0:
            p.setPen(QColor(COLORS['text_dim'])); p.setFont(QFont("Segoe UI", 11))
            p.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter, t("waveform.empty"))
            p.end(); return

        # Cache waveform image
        if self._cache is None or self._cache_w != w:
            self._cache = self._render_wave(w, h); self._cache_w = w
        p.drawImage(0, 0, self._cache)

        # Clip highlight (green)
        if self._clip_hl_start is not None and self._clip_hl_end is not None:
            x1, x2 = self._sample_to_x(self._clip_hl_start), self._sample_to_x(self._clip_hl_end)
            p.fillRect(x1, 0, x2 - x1, h, QColor(22, 199, 154, 30))
            p.setPen(QPen(QColor(COLORS['clip_highlight']), 1, Qt.PenStyle.DashLine))
            p.drawLine(x1, 0, x1, h); p.drawLine(x2, 0, x2, h)

        # Selection (red)
        if self.selection_start is not None and self.selection_end is not None:
            s, en = min(self.selection_start, self.selection_end), max(self.selection_start, self.selection_end)
            x1, x2 = self._sample_to_x(s), self._sample_to_x(en)
            p.fillRect(x1, 0, x2 - x1, h, QColor(233, 69, 96, 40))
            p.setPen(QPen(QColor(COLORS['selection']), 1))
            p.drawLine(x1, 0, x1, h); p.drawLine(x2, 0, x2, h)

        # Playhead
        px = self._sample_to_x(self._playhead)
        p.setPen(QPen(QColor(COLORS['playhead']), 2))
        p.drawLine(px, 0, px, h)
        p.end()

    def _render_wave(self, w, h):
        img = QImage(w, h, QImage.Format.Format_ARGB32_Premultiplied)
        img.fill(QColor(COLORS['bg_dark']))
        if self.audio_data is None: return img
        p = QPainter(img)
        mono = np.mean(self.audio_data, axis=1) if self.audio_data.ndim > 1 else self.audio_data
        n = len(mono); step = max(1, n // w)
        mid = h // 2
        p.setPen(QPen(QColor(COLORS['accent']), 1))
        for x in range(w):
            i0, i1 = x * step, min((x + 1) * step, n)
            if i0 >= n: break
            chunk = mono[i0:i1]
            mn, mx = float(np.min(chunk)), float(np.max(chunk))
            y1 = int(mid - mx * mid * 0.9)
            y2 = int(mid - mn * mid * 0.9)
            p.drawLine(x, y1, x, y2)
        # Center line
        p.setPen(QPen(QColor(COLORS['border']), 1, Qt.PenStyle.DotLine))
        p.drawLine(0, mid, w, mid)
        p.end(); return img

    def resizeEvent(self, e):
        self._cache = None; super().resizeEvent(e)
