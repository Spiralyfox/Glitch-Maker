"""Waveform display — zoom via mouse wheel, pixel buffer rendering, anchor cursor, markers."""
from utils.logger import get_logger
_log = get_logger("waveform")
import numpy as np
from PyQt6.QtWidgets import QWidget, QScrollBar, QInputDialog
from PyQt6.QtCore import Qt, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QImage, QFont, QPolygonF
from utils.config import COLORS
from utils.translator import t


def _parse_color(hex_str):
    """Convertit un code hex (#RRGGBB) en tuple (R,G,B)."""
    h = hex_str.lstrip('#')
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


class WaveformWidget(QWidget):
    position_clicked = pyqtSignal(int)   # click → set anchor
    selection_changed = pyqtSignal(int, int)  # drag → selection
    drag_started = pyqtSignal()  # mouse down starts a drag
    zoom_changed = pyqtSignal(float, float)  # (zoom, offset) — for external scrollbar
    marker_added = pyqtSignal(str, int)  # (name, position)
    cut_silence_requested = pyqtSignal(int, int)  # (start, end) — replace with silence
    cut_splice_requested = pyqtSignal(int, int)   # (start, end) — remove and splice

    def __init__(self, parent=None):
        """Initialise le widget waveform avec zoom, grille, selection, marqueurs."""
        super().__init__(parent)
        self.audio_data: np.ndarray | None = None
        self.sample_rate = 44100
        self.selection_start: int | None = None
        self.selection_end: int | None = None
        self._clip_hl_start: int | None = None
        self._clip_hl_end: int | None = None
        self._playhead: int = 0
        self._anchor: int | None = None
        self._dragging = False
        self._cache: QImage | None = None
        self._cache_w = 0
        self._cache_h = 0
        self._cache_zoom = 0
        self._cache_offset = 0

        # Zoom state
        self._zoom: float = 1.0
        self._offset: float = 0.0
        self._max_zoom: float = 100.0
        
        # Vertical Zoom
        self._v_zoom: float = 1.0

        # Beat grid
        self._grid_enabled = False
        self._grid_bpm = 120.0
        self._grid_beats_per_bar = 4
        self._grid_subdiv = 1
        self._grid_offset_ms = 0.0

        # Markers (step 36)
        self._markers: list[dict] = []  # [{name, position, color}]
        self._marker_colors = ["#ff6b6b", "#ffd93d", "#6bcb77", "#4d96ff",
                                "#ff85a1", "#48bfe3", "#e07c24", "#b5179e"]
        self._marker_idx = 0
        self._right_click_sample = None
        self._show_freq_scale = True
        self._scale_w = 40

        # Precompute colors
        self._wave_rgb = _parse_color(COLORS['accent'])
        self._bg_rgb = _parse_color(COLORS['bg_dark'])
        self._border_rgb = _parse_color(COLORS['border'])
        self.setMinimumHeight(120)
        self.setCursor(Qt.CursorShape.CrossCursor)

    def set_show_freq_scale(self, show: bool):
        """Affiche ou cache l'échelle de fréquence (0 Hz -> SR/2)."""
        if self._show_freq_scale != show:
            self._show_freq_scale = show
            self._cache = None
            self.update()

    def set_grid(self, enabled, bpm=120.0, beats=4, subdiv=1, offset_ms=0.0):
        """Configure la grille de temps (activer, BPM, beats, subdivisions)."""
        self._grid_enabled = enabled
        self._grid_bpm = max(20, bpm)
        self._grid_beats_per_bar = max(1, beats)
        self._grid_subdiv = max(1, subdiv)
        self._grid_offset_ms = offset_ms
        self.update()

    def set_scroll_offset(self, offset):
        """Set offset from external scrollbar (0.0–1.0)."""
        visible = 1.0 / self._zoom
        new_off = max(0.0, min(offset, 1.0 - visible))
        if abs(new_off - self._offset) > 0.0001:
            self._offset = new_off
            self._cache = None
            self.update()

    def set_audio(self, data, sr):
        """Charge les données audio à afficher et réinitialise le zoom."""
        self.audio_data = data
        self.sample_rate = sr
        self._cache = None
        self.update()

    def set_playhead(self, pos):
        """Met a jour la position du playhead (ligne verte)."""
        self._playhead = pos
        self.update()

    def set_selection(self, s, e):
        """Definit la zone de selection (debut, fin en samples). Accepte None."""
        self.selection_start = s if s is not None else None
        self.selection_end = e if e is not None else None
        self.update()

    def set_clip_highlight(self, s, e):
        """Met en surbrillance un clip (bordure verte pointillée)."""
        self._clip_hl_start, self._clip_hl_end = s, e
        self.update()

    def set_anchor(self, pos):
        """Definit la position du curseur ancre (ligne bleue)."""
        self._anchor = pos
        self.update()

    def clear_all(self):
        """Reinitialise la waveform (supprime audio, selection, zoom)."""
        self.selection_start = self.selection_end = None
        self._anchor = None
        self._clip_hl_start = self._clip_hl_end = None
        self.update()

    def clear_selection(self):
        """Efface la selection sans toucher au reste."""
        self.selection_start = self.selection_end = None
        self.update()

    @property
    def bpm(self):
        return self._grid_bpm

    @bpm.setter
    def bpm(self, val):
        self._grid_bpm = max(20, val)
        self._cache = None
        self.update()

    @property
    def grid_subdivisions(self):
        return self._grid_subdiv

    @grid_subdivisions.setter
    def grid_subdivisions(self, val):
        self._grid_subdiv = max(1, val)
        self._cache = None
        self.update()

    def reset_zoom(self):
        """Reset zoom to full view."""
        self._zoom = 1.0
        self._offset = 0.0
        self._v_zoom = 1.0
        self._cache = None
        self.update()
        self.zoom_changed.emit(self._zoom, self._offset)

    # ── Markers (step 36) ──

    def add_marker(self, name: str, position: int, color: str | None = None):
        """Add a named marker at a sample position."""
        if color is None:
            color = self._marker_colors[self._marker_idx % len(self._marker_colors)]
            self._marker_idx += 1
        self._markers.append({"name": name, "position": position, "color": color})
        self.marker_added.emit(name, position)
        self.update()

    def remove_marker(self, name: str):
        """Remove a marker by name."""
        self._markers = [m for m in self._markers if m["name"] != name]
        self.update()

    def clear_markers(self):
        """Remove all markers."""
        self._markers.clear()
        self._marker_idx = 0
        self.update()

    def get_markers(self) -> list[dict]:
        """Return sorted marker list."""
        return sorted(self._markers, key=lambda m: m["position"])

    def next_marker(self) -> int | None:
        """Return position of next marker after current anchor/playhead."""
        pos = self._anchor if self._anchor is not None else self._playhead
        markers = sorted(self._markers, key=lambda m: m["position"])
        for m in markers:
            if m["position"] > pos + 100:
                return m["position"]
        return markers[0]["position"] if markers else None

    def prev_marker(self) -> int | None:
        """Return position of previous marker before current anchor/playhead."""
        pos = self._anchor if self._anchor is not None else self._playhead
        markers = sorted(self._markers, key=lambda m: m["position"], reverse=True)
        for m in markers:
            if m["position"] < pos - 100:
                return m["position"]
        return markers[0]["position"] if markers else None

    # ── Zoom coordinate mapping ──

    def _visible_range(self):
        """Return (start_sample, end_sample) of the currently visible portion."""
        if self.audio_data is None:
            return 0, 0
        n = len(self.audio_data)
        visible_frac = 1.0 / self._zoom
        start_frac = self._offset
        end_frac = min(start_frac + visible_frac, 1.0)
        return int(start_frac * n), int(end_frac * n)

    def _pos_to_sample(self, x):
        """Convert widget x to sample index (accounting for zoom and scale margin)."""
        if self.audio_data is None:
            return 0
        margin = self._scale_w if self._show_freq_scale else 0
        w_eff = max(1, self.width() - margin)
        n = len(self.audio_data)
        vs, ve = self._visible_range()
        visible_len = max(ve - vs, 1)
        frac = max(0.0, min((x - margin) / w_eff, 1.0))
        return int(vs + frac * visible_len)

    def _sample_to_x(self, s):
        """Convert sample index to widget x (accounting for zoom and scale margin)."""
        if self.audio_data is None or len(self.audio_data) == 0:
            return 0
        margin = self._scale_w if self._show_freq_scale else 0
        w_eff = max(1, self.width() - margin)
        vs, ve = self._visible_range()
        visible_len = max(ve - vs, 1)
        return margin + int((s - vs) / visible_len * w_eff)

    # ── Mouse events ──

    def mousePressEvent(self, e):
        """Debut de selection ou positionnement du curseur."""
        if e.button() == Qt.MouseButton.LeftButton and self.audio_data is not None:
            self._dragging = True
            pos = self._pos_to_sample(e.position().x())
            self.selection_start = pos
            self.selection_end = pos
            self._clip_hl_start = None
            self._clip_hl_end = None
            self.drag_started.emit()
            self.update()
        elif e.button() == Qt.MouseButton.RightButton:
            # Store right-click position for contextMenuEvent
            self._right_click_sample = self._pos_to_sample(e.position().x()) if self.audio_data is not None else None
            e.accept()

    def mouseMoveEvent(self, e):
        """Mise a jour de la selection pendant le drag."""
        if self._dragging and self.audio_data is not None:
            self.selection_end = self._pos_to_sample(e.position().x())
            self.update()

    def mouseReleaseEvent(self, e):
        """Fin du drag — emet selection_changed ou position_clicked."""
        if self._dragging:
            self._dragging = False
            if self.selection_start is not None and self.selection_end is not None:
                s = min(self.selection_start, self.selection_end)
                en = max(self.selection_start, self.selection_end)
                if abs(en - s) < 10:
                    self._anchor = s
                    self.selection_start = self.selection_end = None
                    self.position_clicked.emit(s)
                else:
                    self.selection_start, self.selection_end = s, en
                    self._anchor = None
                    self.selection_changed.emit(s, en)
            self.update()

    def contextMenuEvent(self, e):
        """Right-click: cut (if inside selection), marker add/delete/clear — always available."""
        if self.audio_data is None:
            return
        e.accept()
        # Use stored right-click sample position (more reliable than contextMenu event pos)
        pos = getattr(self, '_right_click_sample', None)
        if pos is None:
            pos = self._pos_to_sample(e.pos().x())
        from PyQt6.QtWidgets import QMenu
        menu = QMenu(self)
        menu.setStyleSheet(
            f"QMenu {{ background: {COLORS['bg_panel']}; color: {COLORS['text']};"
            f" border: 1px solid {COLORS['border']}; }}"
            f"QMenu::item {{ padding: 4px 16px; }}"
            f"QMenu::item:selected {{ background: {COLORS['accent']}; color: white; }}")

        # ── Cut options if inside a red selection ──
        a_cut_silence = None
        a_cut_splice = None
        has_sel = (self.selection_start is not None and self.selection_end is not None
                   and abs(self.selection_end - self.selection_start) > 10)
        if has_sel:
            s = min(self.selection_start, self.selection_end)
            en = max(self.selection_start, self.selection_end)
            if s <= pos <= en:
                a_cut_silence = menu.addAction("✂ " + t("cut.replace_silence"))
                a_cut_splice = menu.addAction("✂ " + t("cut.splice"))
                menu.addSeparator()

        # ── Marker options (always available) ──
        a_add = menu.addAction("📌 " + t("marker.add_title"))
        a_del = None
        near = None
        for m in self._markers:
            mx = self._sample_to_x(m["position"])
            if abs(mx - e.pos().x()) < 10:
                near = m; break
        if near:
            a_del = menu.addAction(f"✕ Remove '{near['name']}'")
        if self._markers:
            menu.addSeparator()
            a_clear = menu.addAction(t("marker.clear_all"))
        else:
            a_clear = None

        action = menu.exec(e.globalPos())
        if action is None:
            return
        if action == a_cut_silence and has_sel:
            s = min(self.selection_start, self.selection_end)
            en = max(self.selection_start, self.selection_end)
            self.cut_silence_requested.emit(s, en)
        elif action == a_cut_splice and has_sel:
            s = min(self.selection_start, self.selection_end)
            en = max(self.selection_start, self.selection_end)
            self.cut_splice_requested.emit(s, en)
        elif action == a_add:
            name, ok = QInputDialog.getText(self, t("marker.add_title"),
                                            t("marker.add_prompt"),
                                            text=f"M{len(self._markers)+1}")
            if ok and name:
                self.add_marker(name, pos)
        elif action == a_del and near:
            self.remove_marker(near["name"])
        elif action == a_clear:
            self.clear_markers()

    def wheelEvent(self, e):
        """Mouse wheel → zoom in/out, centered on cursor position."""
        if self.audio_data is None:
            return
        delta = e.angleDelta().y()
        if delta == 0:
            return

        # Check if mouse is over Frequency Scale -> Vertical Zoom
        if self._show_freq_scale and e.position().x() < self._scale_w:
            factor = 1.1 if delta > 0 else 1.0 / 1.1
            self._v_zoom = max(1.0, min(self._v_zoom * factor, 100.0))
            self._cache = None
            self.update()
            return

        # Horizontal Zoom
        # Cursor position as fraction of visible range
        cursor_x_frac = e.position().x() / max(self.width(), 1)

        old_zoom = self._zoom
        factor = 1.2 if delta > 0 else 1.0 / 1.2
        new_zoom = max(1.0, min(self._zoom * factor, self._max_zoom))

        if new_zoom == old_zoom:
            return

        # Keep the sample under cursor at the same screen position
        old_visible = 1.0 / old_zoom
        new_visible = 1.0 / new_zoom
        cursor_sample_frac = self._offset + cursor_x_frac * old_visible
        new_offset = cursor_sample_frac - cursor_x_frac * new_visible
        new_offset = max(0.0, min(new_offset, 1.0 - new_visible))

        self._zoom = new_zoom
        self._offset = new_offset
        self._cache = None
        self.update()
        self.zoom_changed.emit(self._zoom, self._offset)
        e.accept()

    # ── Paint ──

    def paintEvent(self, e):
        """Dessine la waveform, grille, selection, playhead, curseur."""
        p = QPainter(self)
        try:
            w, h = self.width(), self.height()
            p.fillRect(0, 0, w, h, QColor(COLORS['bg_dark']))

            if self.audio_data is None or len(self.audio_data) == 0:
                p.setPen(QColor(COLORS['text_dim']))
                p.setFont(QFont("Segoe UI", 11))
                p.drawText(0, 0, w, h, Qt.AlignmentFlag.AlignCenter, t("waveform.empty"))
                return

            # Cache waveform image
            margin = self._scale_w if self._show_freq_scale else 0
            
            # Clip drawing to waveform area (exclude scale)
            p.setClipRect(margin, 0, w - margin, h)

            w_wave = w - margin
            if (self._cache is None or self._cache_w != w_wave or self._cache_h != h
                    or self._cache_zoom != self._zoom or self._cache_offset != self._offset
                    or getattr(self, '_cache_v_zoom', 1.0) != self._v_zoom):
                self._cache = self._render_wave(w_wave, h)
                self._cache_w = w_wave
                self._cache_h = h
                self._cache_zoom = self._zoom
                self._cache_offset = self._offset
                self._cache_v_zoom = self._v_zoom
            p.drawImage(margin, 0, self._cache)

            # ── Beat grid ──
            if self._grid_enabled and self.audio_data is not None and self._grid_bpm > 0:
                vs, ve = self._visible_range()
                sr = self.sample_rate
                spb = sr * 60.0 / self._grid_bpm
                sp_sub = spb / self._grid_subdiv
                off = int(self._grid_offset_ms * sr / 1000.0)

                if sp_sub > 1:
                    # High-visibility grid colors
                    bar_pen = QPen(QColor(255, 255, 255, 80), 1)
                    beat_pen = QPen(QColor(255, 255, 255, 45), 1)
                    sub_pen = QPen(QColor(255, 255, 255, 28), 1)
                    font = QFont("Consolas", 7)
                    p.setFont(font)

                    adj_vs = vs - off
                    first_sub = int((adj_vs / sp_sub)) * sp_sub + off
                    if first_sub < vs:
                        first_sub += int(sp_sub)
                    gp = first_sub

                    while gp <= ve:
                        x = self._sample_to_x(int(gp))
                        if 0 <= x <= w:
                            beat_in_song = (gp - off) / spb
                            bar_num = int(beat_in_song / self._grid_beats_per_bar)
                            beat_in_bar = beat_in_song - bar_num * self._grid_beats_per_bar
                            is_bar = abs(beat_in_bar) < 0.01 or abs(beat_in_bar - self._grid_beats_per_bar) < 0.01
                            is_beat = abs(beat_in_bar - round(beat_in_bar)) < 0.01

                            if is_bar:
                                p.setPen(bar_pen)
                                p.drawLine(x, 0, x, h)
                                p.setPen(QColor(255, 255, 255, 70))
                                p.drawText(x + 3, 10, str(bar_num + 1))
                            elif is_beat:
                                p.setPen(beat_pen)
                                p.drawLine(x, 0, x, h)
                            else:
                                p.setPen(sub_pen)
                                p.drawLine(x, 0, x, h)
                        gp += sp_sub

            # Clip highlight (green, dashed)
            if self._clip_hl_start is not None and self._clip_hl_end is not None:
                x1 = self._sample_to_x(self._clip_hl_start)
                x2 = self._sample_to_x(self._clip_hl_end)
                if x2 > 0 and x1 < w:
                    p.fillRect(max(x1, 0), 0, min(x2, w) - max(x1, 0), h, QColor(22, 199, 154, 30))
                    p.setPen(QPen(QColor(COLORS['clip_highlight']), 1, Qt.PenStyle.DashLine))
                    if 0 <= x1 <= w: p.drawLine(x1, 0, x1, h)
                    if 0 <= x2 <= w: p.drawLine(x2, 0, x2, h)

            # Selection (red)
            if self.selection_start is not None and self.selection_end is not None:
                s = min(self.selection_start, self.selection_end)
                en = max(self.selection_start, self.selection_end)
                x1, x2 = self._sample_to_x(s), self._sample_to_x(en)
                if x2 > 0 and x1 < w:
                    p.fillRect(max(x1, 0), 0, min(x2, w) - max(x1, 0), h, QColor(233, 69, 96, 40))
                    p.setPen(QPen(QColor(COLORS['selection']), 1))
                    if 0 <= x1 <= w: p.drawLine(x1, 0, x1, h)
                    if 0 <= x2 <= w: p.drawLine(x2, 0, x2, h)

            # Blue anchor cursor
            has_selection = (self.selection_start is not None and self.selection_end is not None
                             and abs(self.selection_end - self.selection_start) > 10)
            if self._anchor is not None and not has_selection:
                ax = self._sample_to_x(self._anchor)
                if -5 <= ax <= w + 5:
                    p.setPen(QPen(QColor("#3b82f6"), 2))
                    p.drawLine(ax, 0, ax, h)
                    p.setBrush(QColor("#3b82f6"))
                    p.setPen(Qt.PenStyle.NoPen)
                    tri = QPolygonF([QPointF(ax - 4, 0), QPointF(ax + 4, 0), QPointF(ax, 6)])
                    p.drawPolygon(tri)

            # Green playhead
            px = self._sample_to_x(self._playhead)
            if -2 <= px <= w + 2:
                p.setPen(QPen(QColor(COLORS['playhead']), 2))
                p.drawLine(px, 0, px, h)

            # ── Markers (step 36) ──
            if self._markers:
                marker_font = QFont("Segoe UI", 7, QFont.Weight.Bold)
                p.setFont(marker_font)
                for m in self._markers:
                    mx = self._sample_to_x(m["position"])
                    if -5 <= mx <= w + 5:
                        mc = QColor(m["color"])
                        # Vertical line
                        p.setPen(QPen(mc, 1, Qt.PenStyle.DashDotLine))
                        p.drawLine(mx, 0, mx, h)
                        # Flag at top
                        p.setPen(Qt.PenStyle.NoPen)
                        p.setBrush(mc)
                        flag_w = min(50, max(20, len(m["name"]) * 6 + 8))
                        p.drawRoundedRect(mx, 0, flag_w, 14, 2, 2)
                        # Text
                        p.setPen(QColor("white"))
                        p.drawText(mx + 3, 10, m["name"])

            # Zoom level indicator (bottom-right text)
            if self._zoom > 1.01:
                p.setPen(QColor(COLORS['text_dim']))
                p.setFont(QFont("Consolas", 8))
                p.drawText(w - 60, h - 4, f"x{self._zoom:.1f}")

            # Disable clipping for scale
            p.setClipping(False)

            # ── Frequency Scale (-SR/2 -> +SR/2) ──
            if self._show_freq_scale:
                p.setPen(QPen(QColor(COLORS['border']), 1))
                p.drawLine(margin - 1, 0, margin - 1, h)
                p.setFont(QFont("Consolas", 7))
                
                sr_half = self.sample_rate / 2
                
                # Apply vertical zoom to range
                visible_sr_half = sr_half / self._v_zoom
                
                # Draw 0 Hz
                y0 = int(h / 2)
                p.setPen(QColor(COLORS['text_dim']))
                p.drawLine(margin - 5, y0, margin - 1, y0)
                p.drawText(2, y0 + 3, "0 Hz")

                # Adaptive Step
                # Aim for ~8-10 ticks
                rough_step = visible_sr_half / 8
                import math
                if rough_step > 0:
                    mag = 10 ** math.floor(math.log10(rough_step))
                    base = rough_step / mag
                    if base < 2: step = 1 * mag
                    elif base < 5: step = 2 * mag
                    else: step = 5 * mag
                    step_hz = max(1, int(step))
                else:
                    step_hz = 1000

                # Go up from 0
                f = step_hz
                while f < visible_sr_half:
                    ratio = f / visible_sr_half
                    y_up = int((h / 2) * (1 - ratio))
                    y_down = int((h / 2) * (1 + ratio))
                    
                    # Label context
                    if f >= 1000:
                        txt = f"{f/1000:.0f}k" if f % 1000 == 0 else f"{f/1000:.1f}k"
                    else:
                        txt = str(f)
                    
                    # Draw Up (+f)
                    if y_up > 10:
                        p.drawLine(margin - 5, y_up, margin - 1, y_up)
                        p.drawText(2, y_up + 3, txt)
                        
                    # Draw Down (-f)
                    if y_down < h - 10:
                        p.drawLine(margin - 5, y_down, margin - 1, y_down)
                        p.drawText(2, y_down + 3, f"-{txt}")
                        
                    f += step_hz

        except Exception as ex:
            _log.warning("Waveform paintEvent: %s", ex)
        finally:
            p.end()

    def _calc_display_data(self, w):
        """
        Calculate min/max arrays (or raw mono) for the current visible range.
        Returns: (mode, data)
          mode='high': data is mono array (for polyline)
          mode='low': data is (mins, maxs) arrays (for envelope)
          mode='empty': data is None
        """
        if self.audio_data is None or len(self.audio_data) == 0:
            return 'empty', None

        vs, ve = self._visible_range()
        visible = self.audio_data[vs:ve]
        if len(visible) == 0:
            return 'empty', None

        # Convert to mono
        mono = np.mean(visible, axis=1) if visible.ndim > 1 else visible
        n = len(mono)

        # High Zoom (few samples) -> Return raw
        if n < w:
            return 'high', mono
            
        # Low Zoom -> Downsample
        step = max(1, n // w)
        cols = min(w, n // step if step > 0 else w)
        if cols <= 0:
            return 'empty', None

        usable = cols * step
        reshaped = mono[:usable].reshape(cols, step)
        mins = np.min(reshaped, axis=1)
        maxs = np.max(reshaped, axis=1)
        
        return 'low', (mins, maxs)

    def _render_wave(self, w, h):
        """Render waveform using cached display data if available."""
        # Standard background
        buf = np.zeros((h, w, 4), dtype=np.uint8)
        br, bg, bb = self._bg_rgb
        buf[:, :, 0] = bb
        buf[:, :, 1] = bg
        buf[:, :, 2] = br
        buf[:, :, 3] = 255
        
        # Center line
        mid = h // 2
        bb2, bg2, br2 = self._border_rgb[2], self._border_rgb[1], self._border_rgb[0]
        buf[mid, ::2, 0] = bb2 # Blue
        buf[mid, ::2, 1] = bg2 # Green
        buf[mid, ::2, 2] = br2 # Red

        # Check if we need to recompute data
        # Data depends on: audio_data, visible_range (zoom, offset), width. 
        # NOT on h or v_zoom.
        
        current_data_key = (self._zoom, self._offset, w, id(self.audio_data))
        
        if getattr(self, '_data_cache_key', None) != current_data_key:
            self._data_mode, self._data_val = self._calc_display_data(w)
            self._data_cache_key = current_data_key
            
        if self._data_mode == 'empty':
            return QImage(buf.data, w, h, w * 4, QImage.Format.Format_ARGB32).copy()

        img = QImage(buf.data, w, h, w * 4, QImage.Format.Format_ARGB32).copy()
        p = QPainter(img)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        color = QColor(*self._wave_rgb)
        p.setPen(QPen(color, 1))

        if self._data_mode == 'high':
            # Draw Polyline from mono data
            mono = self._data_val
            # Apply Vertical Zoom
            if self._v_zoom > 1.0:
                mono = mono * self._v_zoom
                
            n = len(mono)
            xs = np.linspace(0, w, n)
            ys = mid - mono * mid * 0.9
            
            points = [QPointF(x, y) for x, y in zip(xs, ys)]
            p.drawPolyline(points)
            p.end()
            return img
            
        elif self._data_mode == 'low':
            mins, maxs = self._data_val
            
            # Apply Vertical Zoom locally
            if self._v_zoom > 1.0:
                mins = mins * self._v_zoom
                maxs = maxs * self._v_zoom
            
            # Map to screen Y
            y_top = np.clip((mid - maxs * mid * 0.9).astype(np.int32), 0, h - 1)
            y_bot = np.clip((mid - mins * mid * 0.9).astype(np.int32), 0, h - 1)
            yt = np.minimum(y_top, y_bot)
            yb = np.maximum(y_top, y_bot)

            # Determine LOD Strategy
            # self.audio_data length vs width?
            # actually we can infer 'step' from earlier or recalculate.
            # step = max(1, n // w). But we don't have n here easily without peeking cache logic.
            # However, we know len(mins) == cols.
            # And cols <= w.
            # The density 'step' was calculated in _calc_display_data.
            # We should probably return 'step' from _calc_display_data or re-estimate it here?
            # We can pass 'step' in 'low' tuple.
            
            # Or simpler: we can just check if we are truly zoomed out?
            # Actually, the user's issue is likely simpler:
            # If we have a cached mins/maxs, it is ALREADY downsampled to ~w pixels.
            # So drawing it via QPainter shouldn't be that slow (only ~w points).
            # UNLESS w is very large (4k screen?).
            
            # BUT, the user specifically mentioned "trop de traits".
            # Let's trust the user and use Hybrid approach.
            
            # We need the 'step' to decide.
            # Let's retrieve step from cache tuple? Or modify _calc_display_data.
            # Alternatively, re-calculate n?
            # visible_len = ve - vs.
            # step = visible_len // w.
            
            vs, ve = self._visible_range()
            visible_len = ve - vs
            step = max(1, visible_len // w)
            
            # LOD Threshold:
            # If step > 4 (compressed > 4 samples per pixel), use Numpy Buffer (Fast).
            # If step <= 4 (getting closer to 1:1), use QPainter (Smooth).
            
            if step > 4:
                 # ── Fast Mode (Numpy Buffer) ──
                p.end() # Don't use QPainter for this part
                
                cols = len(mins)
                rows = np.arange(h, dtype=np.int32).reshape(h, 1)
                mask = (rows >= yt[np.newaxis, :]) & (rows <= yb[np.newaxis, :])
                
                # Colors
                wr, wg, wb = self._wave_rgb
                
                # Slice interest region
                roi = buf[:, :cols]
                roi[mask, 0] = wb
                roi[mask, 1] = wg
                roi[mask, 2] = wr
                
                return QImage(buf.data, w, h, w * 4, QImage.Format.Format_ARGB32).copy()
            
            else:
                 # ── Smooth Mode (QPainter) ──
                cols = len(mins)
                # We need floats for QPainter
                # Re-map floats from raw values (or ints if we want pixel perfect?)
                # We used floats int previously for smoothness.
                
                y_max_f = mid - maxs * mid * 0.9
                y_min_f = mid - mins * mid * 0.9
                
                xs = np.arange(cols, dtype=np.float64)
                
                points_top = [QPointF(x, y) for x, y in zip(xs, y_max_f)]
                points_bot = [QPointF(x, y) for x, y in zip(xs, y_min_f)]
                
                # Draw filled envelope
                poly = QPolygonF(points_top + points_bot[::-1])
                p.setBrush(QBrush(color))
                p.setPen(Qt.PenStyle.NoPen)
                p.drawPolygon(poly)
                
                # Draw outlines
                p.setPen(QPen(color, 1))
                p.drawPolyline(QPolygonF(points_top))
                p.drawPolyline(QPolygonF(points_bot))

        p.end()
        return img

        # Center line (dotted)
        bb2, bg2, br2 = self._border_rgb[2], self._border_rgb[1], self._border_rgb[0]
        buf[mid, ::2, 0] = bb2
        buf[mid, ::2, 1] = bg2
        buf[mid, ::2, 2] = br2

        img = QImage(buf.data, w, h, w * 4, QImage.Format.Format_ARGB32)
        return img.copy()

    def resizeEvent(self, e):
        """Invalide le cache waveform quand le widget est redimensionne."""
        self._cache = None
        super().resizeEvent(e)
