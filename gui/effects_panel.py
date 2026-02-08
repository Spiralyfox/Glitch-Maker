"""
Effects panel (left sidebar) — search bar + filter, effects list, preset accordion.
Search matches effect names, preset names, and effect descriptions (keyword search).
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QPushButton, QScrollArea,
    QFrame, QHBoxLayout, QToolTip, QLineEdit, QMenu, QCheckBox
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer, QPoint
from PyQt6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QAction
from utils.config import COLORS


class IconLabel(QWidget):
    def __init__(self, letter, color, parent=None):
        super().__init__(parent)
        self.letter, self.color = letter, color
        self.setFixedSize(24, 24)
    def paintEvent(self, e):
        p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
        p.setBrush(QBrush(QColor(self.color))); p.setPen(Qt.PenStyle.NoPen)
        p.drawRoundedRect(1, 1, 22, 22, 5, 5)
        p.setPen(QColor("white")); p.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        p.drawText(1, 1, 22, 22, Qt.AlignmentFlag.AlignCenter, self.letter); p.end()


class EffectButton(QWidget):
    clicked = pyqtSignal()
    def __init__(self, letter, color, name, cat_key, parent=None):
        super().__init__(parent)
        self.effect_name = name
        self._cat_key = cat_key
        self.setFixedHeight(30)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        lo = QHBoxLayout(self); lo.setContentsMargins(6, 1, 6, 1); lo.setSpacing(8)
        lo.addWidget(IconLabel(letter, color))
        lbl = QLabel(name); lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: 11px;")
        lo.addWidget(lbl); lo.addStretch()
        self._hover = False
        self._tip_timer = QTimer(); self._tip_timer.setSingleShot(True)
        self._tip_timer.setInterval(1000)
        self._tip_timer.timeout.connect(self._show_tip)

    def enterEvent(self, e):
        self._hover = True; self.update(); self._tip_timer.start()
    def leaveEvent(self, e):
        self._hover = False; self.update(); self._tip_timer.stop(); QToolTip.hideText()
    def _show_tip(self):
        from utils.translator import t
        detail = t(f"cat.{self._cat_key}.detail")
        if detail and self._hover:
            pos = self.mapToGlobal(QPoint(self.width() + 4, 0))
            QToolTip.showText(pos, detail, self, self.rect(), 8000)
    def paintEvent(self, e):
        if self._hover:
            p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setBrush(QBrush(QColor(COLORS['button_hover'])))
            p.setPen(QPen(QColor(COLORS['accent']), 1))
            p.drawRoundedRect(1, 1, self.width()-2, self.height()-2, 4, 4); p.end()
        super().paintEvent(e)
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton: self.clicked.emit()


# ── Preset widgets ──

class PresetItem(QWidget):
    clicked = pyqtSignal(str)
    def __init__(self, name, description="", parent=None):
        super().__init__(parent)
        self._name = name; self.setFixedHeight(24)
        self.setCursor(Qt.CursorShape.PointingHandCursor); self._hover = False
        lo = QHBoxLayout(self); lo.setContentsMargins(16, 1, 6, 1); lo.setSpacing(4)
        lbl = QLabel(name); lbl.setStyleSheet(f"color: {COLORS['text']}; font-size: 10px;")
        lo.addWidget(lbl)
        if description:
            desc = QLabel(f"— {description}")
            desc.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 9px;")
            lo.addWidget(desc)
        lo.addStretch()
    def enterEvent(self, e): self._hover = True; self.update()
    def leaveEvent(self, e): self._hover = False; self.update()
    def paintEvent(self, e):
        if self._hover:
            p = QPainter(self); p.setRenderHint(QPainter.RenderHint.Antialiasing)
            p.setBrush(QBrush(QColor(COLORS['button_hover']))); p.setPen(Qt.PenStyle.NoPen)
            p.drawRoundedRect(1, 1, self.width()-2, self.height()-2, 3, 3); p.end()
        super().paintEvent(e)
    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton: self.clicked.emit(self._name)


class TagSection(QWidget):
    preset_clicked = pyqtSignal(str)
    def __init__(self, tag_name, presets, parent=None):
        super().__init__(parent)
        self._expanded = False; self._tag = tag_name
        main_lo = QVBoxLayout(self); main_lo.setContentsMargins(0, 0, 0, 0); main_lo.setSpacing(0)
        self._header = QPushButton(f"▸  {tag_name}  ({len(presets)})")
        self._header.setFixedHeight(26); self._header.setCursor(Qt.CursorShape.PointingHandCursor)
        self._header.setStyleSheet(f"""
            QPushButton {{ background: {COLORS['bg_dark']}; color: {COLORS['text']};
                border: 1px solid {COLORS['border']}; border-radius: 4px;
                font-size: 10px; font-weight: bold; text-align: left; padding-left: 8px; }}
            QPushButton:hover {{ background: {COLORS['button_hover']}; border-color: {COLORS['accent']}; }}
        """)
        self._header.clicked.connect(self._toggle); main_lo.addWidget(self._header)
        self._content = QWidget(); self._content.setVisible(False)
        self._content_lo = QVBoxLayout(self._content)
        self._content_lo.setContentsMargins(0, 2, 0, 2); self._content_lo.setSpacing(1)
        for p in presets:
            item = PresetItem(p["name"], p.get("description", ""))
            item.clicked.connect(self.preset_clicked.emit)
            self._content_lo.addWidget(item)
        main_lo.addWidget(self._content)
    def _toggle(self):
        self._expanded = not self._expanded
        self._content.setVisible(self._expanded)
        arrow = "▾" if self._expanded else "▸"
        self._header.setText(f"{arrow}{self._header.text()[1:]}")


# ── Effects ordered by audio production category ──

EFFECTS = [
    # Basics
    ("R", "#0f3460",  "Reverse",       "reverse"),
    ("U", "#4cc9f0",  "Volume",        "volume"),
    ("L", "#264653",  "Filter",        "filter"),
    # Pitch & Time
    ("P", "#16c79a",  "Pitch Shift",   "pitch_shift"),
    ("T", "#c74b50",  "Time Stretch",  "time_stretch"),
    ("X", "#3d5a80",  "Tape Stop",     "tape_stop"),
    # Distortion
    ("D", "#ff6b35",  "Saturation",    "saturation"),
    ("W", "#b5179e",  "Distortion",    "distortion"),
    ("B", "#533483",  "Bitcrusher",    "bitcrusher"),
    # Modulation
    ("C", "#2a6478",  "Chorus",        "chorus"),
    ("A", "#6d597a",  "Phaser",        "phaser"),
    ("~", "#e07c24",  "Tremolo",       "tremolo"),
    ("M", "#6d597a",  "Ring Mod",      "ring_mod"),
    # Space & Texture
    ("E", "#2a9d8f",  "Delay",         "delay"),
    ("V", "#606c38",  "Vinyl",         "vinyl"),
    ("O", "#e76f51",  "OTT",           "ott"),
    # Glitch
    ("S", "#e94560",  "Stutter",       "stutter"),
    ("G", "#7b2d8e",  "Granular",      "granular"),
    ("K", "#bb3e03",  "Shuffle",       "shuffle"),
    ("F", "#457b9d",  "Buffer Freeze", "buffer_freeze"),
    ("Z", "#9b2226",  "Datamosh",      "datamosh"),
]


class EffectsPanel(QWidget):
    """Sidebar with search, effects and preset accordion blocks."""

    effect_clicked = pyqtSignal(str)
    catalog_clicked = pyqtSignal()
    preset_clicked = pyqtSignal(str)
    preset_new_clicked = pyqtSignal()
    preset_manage_clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(195)
        self._preset_tags: dict[str, list] = {}
        self._all_presets: list[dict] = []
        # Search filter state
        self._show_effects = True
        self._show_presets = True
        self._search_text = ""
        self._build()

    def _build(self):
        lo = QVBoxLayout(self)
        lo.setContentsMargins(6, 8, 6, 6); lo.setSpacing(4)

        tt = QLabel("EFFECTS")
        tt.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        tt.setStyleSheet(f"color: {COLORS['accent']}; letter-spacing: 2px;")
        lo.addWidget(tt)

        btn = QPushButton("?  Catalog")
        btn.setFixedHeight(28); btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setStyleSheet(f"""
            QPushButton {{ background: {COLORS['accent_secondary']}; color: white;
                border: none; border-radius: 5px; font-size: 11px;
                font-weight: bold; text-align: left; padding-left: 10px; }}
            QPushButton:hover {{ background: {COLORS['accent']}; }}
        """)
        btn.clicked.connect(self.catalog_clicked.emit)
        lo.addWidget(btn)

        # ── Search bar + filter ──
        search_row = QHBoxLayout(); search_row.setSpacing(3)
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search...")
        self._search_input.setFixedHeight(26)
        self._search_input.setStyleSheet(f"""
            QLineEdit {{ background: {COLORS['bg_dark']}; color: {COLORS['text']};
                border: 1px solid {COLORS['border']}; border-radius: 4px;
                padding: 0 6px; font-size: 10px; }}
            QLineEdit:focus {{ border-color: {COLORS['accent']}; }}
        """)
        self._search_input.textChanged.connect(self._on_search)
        search_row.addWidget(self._search_input, stretch=1)

        self._filter_btn = QPushButton("⚙")
        self._filter_btn.setFixedSize(26, 26)
        self._filter_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._filter_btn.setStyleSheet(f"""
            QPushButton {{ background: {COLORS['button_bg']}; color: {COLORS['text']};
                border: 1px solid {COLORS['border']}; border-radius: 4px; font-size: 12px; }}
            QPushButton:hover {{ background: {COLORS['button_hover']}; border-color: {COLORS['accent']}; }}
        """)
        self._filter_btn.clicked.connect(self._show_filter_menu)
        search_row.addWidget(self._filter_btn)
        lo.addLayout(search_row)

        lo.addWidget(self._sep())

        self._scroll = QScrollArea(); self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self._scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{ background: {COLORS['bg_dark']}; width: 5px; }}
            QScrollBar::handle:vertical {{ background: {COLORS['scrollbar']}; border-radius: 2px; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        """)
        self._rebuild_scroll_content()
        lo.addWidget(self._scroll)

    def _show_filter_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet(f"""
            QMenu {{ background: {COLORS['bg_medium']}; color: {COLORS['text']};
                border: 1px solid {COLORS['border']}; font-size: 11px; }}
            QMenu::item {{ padding: 5px 14px; }}
            QMenu::item:selected {{ background: {COLORS['accent']}; }}
        """)
        a_eff = menu.addAction("✓  Effects" if self._show_effects else "     Effects")
        a_pre = menu.addAction("✓  Presets" if self._show_presets else "     Presets")
        a_eff.triggered.connect(lambda: self._toggle_filter("effects"))
        a_pre.triggered.connect(lambda: self._toggle_filter("presets"))
        menu.exec(self._filter_btn.mapToGlobal(self._filter_btn.rect().bottomLeft()))

    def _toggle_filter(self, which):
        if which == "effects":
            self._show_effects = not self._show_effects
        else:
            self._show_presets = not self._show_presets
        # Don't allow both off
        if not self._show_effects and not self._show_presets:
            self._show_effects = True
            self._show_presets = True
        self._rebuild_scroll_content()

    def _on_search(self, text):
        self._search_text = text.strip().lower()
        self._rebuild_scroll_content()

    def _effect_matches(self, name, cat_key, query):
        """Check if effect matches search query (name + description keywords)."""
        if not query:
            return True
        if query in name.lower():
            return True
        # Search in catalog description
        from utils.translator import t
        for suffix in ("short", "detail"):
            desc = t(f"cat.{cat_key}.{suffix}").lower()
            if query in desc:
                return True
        return False

    def _preset_matches(self, preset, query):
        """Check if preset matches search query."""
        if not query:
            return True
        if query in preset["name"].lower():
            return True
        if query in preset.get("description", "").lower():
            return True
        # Match by effect names in the preset chain
        for eff in preset.get("effects", []):
            if query in eff.get("name", "").lower():
                return True
        # Match by tags
        for tag in preset.get("tags", []):
            if query in tag.lower():
                return True
        return False

    def _rebuild_scroll_content(self):
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(0, 2, 0, 2); cl.setSpacing(1)
        q = self._search_text
        has_results = False

        # Category groups for visual separators
        CATEGORIES = [
            ("Basics", [0, 1, 2]),
            ("Pitch & Time", [3, 4, 5]),
            ("Distortion", [6, 7, 8]),
            ("Modulation", [9, 10, 11, 12]),
            ("Space & Texture", [13, 14, 15]),
            ("Glitch", [16, 17, 18, 19, 20]),
        ]

        # ── Effects ──
        if self._show_effects:
            if q:
                # Flat search results
                matching = [(l, c, n, k) for l, c, n, k in EFFECTS
                            if self._effect_matches(n, k, q)]
                if matching:
                    has_results = True
                    cl.addWidget(self._section("EFFECTS"))
                    for letter, color, name, cat_key in matching:
                        b = EffectButton(letter, color, name, cat_key)
                        b.clicked.connect(lambda n=name: self.effect_clicked.emit(n))
                        cl.addWidget(b)
            else:
                # Category-grouped view
                for cat_name, indices in CATEGORIES:
                    cat_effects = [EFFECTS[i] for i in indices if i < len(EFFECTS)]
                    if cat_effects:
                        has_results = True
                        cl.addWidget(self._cat_label(cat_name))
                        for letter, color, name, cat_key in cat_effects:
                            b = EffectButton(letter, color, name, cat_key)
                            b.clicked.connect(lambda n=name: self.effect_clicked.emit(n))
                            cl.addWidget(b)

        # ── Presets ──
        if self._show_presets:
            if q:
                # Flat list of matching presets
                matching_presets = [p for p in self._all_presets if self._preset_matches(p, q)]
                if matching_presets:
                    has_results = True
                    cl.addWidget(self._sep())
                    cl.addWidget(self._section("PRESETS"))
                    for p in matching_presets:
                        item = PresetItem(p["name"], p.get("description", ""))
                        item.clicked.connect(self.preset_clicked.emit)
                        cl.addWidget(item)
            else:
                # Normal accordion view
                has_results = True
                cl.addWidget(self._sep())
                cl.addWidget(self._section("PRESETS"))

                # "All" block first
                if self._all_presets:
                    sec = TagSection("All", self._all_presets)
                    sec.preset_clicked.connect(self.preset_clicked.emit)
                    cl.addWidget(sec)

                # Per-tag blocks
                for tag in sorted(self._preset_tags.keys()):
                    presets = self._preset_tags[tag]
                    if not presets:
                        continue
                    sec = TagSection(tag, presets)
                    sec.preset_clicked.connect(self.preset_clicked.emit)
                    cl.addWidget(sec)

        # No results message
        if q and not has_results:
            no = QLabel("No results")
            no.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px; padding: 12px;")
            no.setAlignment(Qt.AlignmentFlag.AlignCenter)
            cl.addWidget(no)

        # Action buttons (always visible when not searching)
        if not q:
            cl.addSpacing(4)
            btn_new = QPushButton("+ New preset")
            btn_new.setFixedHeight(26); btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_new.setStyleSheet(f"""
                QPushButton {{ background: transparent; color: {COLORS['accent']};
                    border: 1px dashed {COLORS['accent']}; border-radius: 4px; font-size: 10px; }}
                QPushButton:hover {{ background: {COLORS['button_hover']}; }}
            """)
            btn_new.clicked.connect(self.preset_new_clicked.emit)
            cl.addWidget(btn_new)

            btn_manage = QPushButton("Manage presets")
            btn_manage.setFixedHeight(24); btn_manage.setCursor(Qt.CursorShape.PointingHandCursor)
            btn_manage.setStyleSheet(f"""
                QPushButton {{ background: transparent; color: {COLORS['text_dim']};
                    border: none; font-size: 10px; text-decoration: underline; }}
                QPushButton:hover {{ color: {COLORS['accent']}; }}
            """)
            btn_manage.clicked.connect(self.preset_manage_clicked.emit)
            cl.addWidget(btn_manage)

        cl.addStretch()
        self._scroll.setWidget(content)

    def set_presets(self, tag_map: dict[str, list], all_presets: list[dict] | None = None):
        self._preset_tags = tag_map
        if all_presets is not None:
            self._all_presets = all_presets
        else:
            seen = set(); self._all_presets = []
            for presets in tag_map.values():
                for p in presets:
                    if p["name"] not in seen:
                        seen.add(p["name"]); self._all_presets.append(p)
            self._all_presets.sort(key=lambda p: p["name"])
        self._rebuild_scroll_content()

    def _section(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {COLORS['text_dim']}; font-size: 9px; "
            f"padding: 8px 0 2px 4px; letter-spacing: 1px;")
        return lbl

    def _cat_label(self, text):
        lbl = QLabel(text)
        lbl.setStyleSheet(
            f"color: {COLORS['text_dim']}; font-size: 8px; font-weight: bold; "
            f"padding: 6px 0 1px 6px; letter-spacing: 1px;")
        return lbl

    def _sep(self):
        s = QFrame(); s.setFrameShape(QFrame.Shape.HLine)
        s.setStyleSheet(f"color: {COLORS['border']};"); return s
