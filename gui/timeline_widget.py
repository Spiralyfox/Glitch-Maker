"""Timeline widget — drag-to-reorder clips, context menu."""
import numpy as np
from PyQt6.QtWidgets import QWidget, QMenu
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont
from utils.config import COLORS
from utils.translator import t

CLIP_COLORS = ["#533483", "#e94560", "#0f3460", "#16c79a", "#ff6b35", "#c74b50"]

class TimelineWidget(QWidget):
    clip_selected = pyqtSignal(str)
    split_requested = pyqtSignal(str, int)
    duplicate_requested = pyqtSignal(str)
    delete_requested = pyqtSignal(str)
    fade_in_requested = pyqtSignal(str)
    fade_out_requested = pyqtSignal(str)
    clips_reordered = pyqtSignal()

    def __init__(self, timeline=None, parent=None):
        super().__init__(parent)
        self.timeline = timeline
        self.sample_rate = 44100
        self.setMinimumHeight(70); self.setMaximumHeight(100)
        self._selected_id: str | None = None
        self._playhead_x = 0
        self._drag_src = None; self._drag_x = 0; self._dragging = False
        self._press_x = 0
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._ctx_menu)

    def set_playhead(self, pos, sr):
        self.sample_rate = sr
        if self.timeline:
            total = self.timeline.total_duration_samples
            self._playhead_x = int(pos / total * self.width()) if total > 0 else 0
        self.update()

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton and self.timeline and self.timeline.clips:
            self._press_x = int(e.position().x())
            clip = self._clip_at(self._press_x)
            if clip:
                self._selected_id = clip.id; self._drag_src = clip; self._dragging = False
                self.clip_selected.emit(clip.id)
            self.update()

    def mouseMoveEvent(self, e):
        if self._drag_src and abs(int(e.position().x()) - self._press_x) > 8:
            self._dragging = True; self._drag_x = int(e.position().x()); self.update()

    def mouseReleaseEvent(self, e):
        if self._dragging and self._drag_src and self.timeline:
            try:
                target = self._clip_at(int(e.position().x()))
                if target and target.id != self._drag_src.id:
                    clips = self.timeline.clips
                    # Verify both clips still exist in the list
                    if self._drag_src in clips and target in clips:
                        src_idx = clips.index(self._drag_src)
                        tgt_idx = clips.index(target)
                        clip = clips.pop(src_idx)
                        # Adjust target index after removal
                        if src_idx < tgt_idx:
                            tgt_idx -= 1
                        clips.insert(tgt_idx, clip)
                        # Recalculate positions sequentially
                        pos = 0
                        for c in clips:
                            c.position = pos
                            pos += c.duration_samples
                        self.clips_reordered.emit()
            except (ValueError, IndexError, RuntimeError) as ex:
                print(f"[timeline] drag error: {ex}")
        self._drag_src = None; self._dragging = False; self.update()

    def _clip_at(self, x):
        if not self.timeline or not self.timeline.clips: return None
        total = self.timeline.total_duration_samples
        if total == 0: return None
        for c in self.timeline.clips:
            x1 = int(c.position / total * self.width())
            x2 = int(c.end_position / total * self.width())
            if x1 <= x <= x2: return c
        return None

    def _ctx_menu(self, pos):
        clip = self._clip_at(pos.x())
        if not clip: return
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background: {COLORS['bg_medium']}; color: {COLORS['text']}; border: 1px solid {COLORS['border']}; font-size: 11px; }}
            QMenu::item {{ padding: 5px 20px; }} QMenu::item:selected {{ background: {COLORS['accent']}; }}
        """)
        cid = clip.id
        total = self.timeline.total_duration_samples
        click_sample = int(pos.x() / self.width() * total) - clip.position if total > 0 else 0
        menu.addAction("Cut here", lambda: self.split_requested.emit(cid, max(1, click_sample)))
        menu.addAction("Duplicate", lambda: self.duplicate_requested.emit(cid))
        menu.addSeparator()
        menu.addAction("Fade In", lambda: self.fade_in_requested.emit(cid))
        menu.addAction("Fade Out", lambda: self.fade_out_requested.emit(cid))
        menu.addSeparator()
        menu.addAction("Delete", lambda: self.delete_requested.emit(cid))
        menu.exec(self.mapToGlobal(pos))

    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        w, h = self.width(), self.height()
        p.fillRect(0, 0, w, h, QColor(COLORS['bg_medium']))

        # Time ruler
        p.setPen(QColor(COLORS['text_dim'])); p.setFont(QFont("Consolas", 8))
        total_s = self.timeline.total_duration_seconds if self.timeline else 0
        if total_s <= 0: total_s = 8
        step = max(1, int(total_s / 8))
        for s in range(0, int(total_s) + 1, step):
            x = int(s / total_s * w) if total_s > 0 else 0
            p.drawText(x + 2, 10, f"{s//60:02d}:{s%60:02d}.00")
            p.drawLine(x, 12, x, h)

        if not self.timeline or not self.timeline.clips:
            p.setPen(QColor(COLORS['text_dim'])); p.setFont(QFont("Segoe UI", 10))
            p.drawText(0, 14, w, h - 14, Qt.AlignmentFlag.AlignCenter, t("timeline.empty"))
            p.end(); return

        total = self.timeline.total_duration_samples
        if total == 0: p.end(); return
        y0 = 14

        for i, c in enumerate(self.timeline.clips):
            x1 = int(c.position / total * w)
            x2 = int(c.end_position / total * w)
            cw = max(x2 - x1, 2)
            col = QColor(c.color if c.color else CLIP_COLORS[i % len(CLIP_COLORS)])
            col.setAlpha(160)
            p.fillRect(x1, y0, cw, h - y0 - 2, col)
            # Mini waveform
            if c.audio_data is not None and len(c.audio_data) > 0 and cw > 4:
                mono = np.mean(c.audio_data, axis=1) if c.audio_data.ndim > 1 else c.audio_data
                step_w = max(1, len(mono) // cw)
                mid = y0 + (h - y0 - 2) // 2
                ah = (h - y0 - 2) // 2 - 2
                p.setPen(QPen(QColor(255, 255, 255, 120), 1))
                for x in range(cw):
                    i0 = x * step_w; i1 = min(i0 + step_w, len(mono))
                    if i0 >= len(mono): break
                    pk = float(np.max(np.abs(mono[i0:i1])))
                    hy = int(pk * ah)
                    p.drawLine(x1 + x, mid - hy, x1 + x, mid + hy)

            # Label
            p.setPen(QColor("white")); p.setFont(QFont("Segoe UI", 8))
            dur = c.duration_seconds
            label = f"{c.name} ({dur:.1f}s)"
            p.drawText(x1 + 4, y0 + 12, label)

            # Selection border
            if c.id == self._selected_id:
                p.setPen(QPen(QColor(COLORS['accent']), 2))
                p.drawRect(x1, y0, cw, h - y0 - 2)

        # Drag ghost
        if self._dragging and self._drag_src:
            p.fillRect(self._drag_x - 20, y0, 40, h - y0 - 2, QColor(108, 92, 231, 80))
            p.setPen(QPen(QColor(COLORS['accent']), 2, Qt.PenStyle.DashLine))
            p.drawLine(self._drag_x, y0, self._drag_x, h - 2)

        # Playhead
        p.setPen(QPen(QColor(COLORS['playhead']), 2))
        p.drawLine(self._playhead_x, 0, self._playhead_x, h)
        p.end()
