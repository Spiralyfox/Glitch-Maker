"""
Main window — Glitch Maker v2.1
21 effects alphabetical, separate audio/language settings, tooltips,
volume effect, improved FFmpeg detection.
"""

import os
import numpy as np
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QFileDialog, QMessageBox, QPushButton, QLabel
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QDragEnterEvent, QDropEvent, QShortcut, QKeySequence

from gui.waveform_widget import WaveformWidget
from gui.timeline_widget import TimelineWidget
from gui.effects_panel import EffectsPanel
from gui.transport_bar import TransportBar
from gui.dialogs import RecordDialog, AboutDialog
from gui.catalog_dialog import CatalogDialog
from gui.settings_dialog import SettingsDialog
from gui.preset_dialog import PresetCreateDialog, PresetManageDialog, TagManageDialog
from gui.effect_dialogs import (
    StutterDialog, BitcrusherDialog, SaturationDialog,
    PitchShiftDialog, TimeStretchDialog, ReverseDialog,
    GranularDialog, TapeStopDialog, BufferFreezeDialog,
    DelayDialog, RingModDialog, FilterDialog,
    OTTDialog, VinylDialog, DatamoshDialog, ShuffleDialog,
    VolumeDialog, ChorusDialog, DistortionDialog,
    PhaserDialog, TremoloDialog
)
from core.audio_engine import (
    load_audio, export_audio, ensure_stereo, get_duration, format_time
)
from core.playback import PlaybackEngine
from core.timeline import Timeline, AudioClip
from core.project import save_project, load_project
from core.preset_manager import PresetManager

from core.effects.stutter import stutter
from core.effects.bitcrusher import bitcrush
from core.effects.saturation import hard_clip, soft_clip, overdrive
from core.effects.reverse import reverse
from core.effects.pitch_shift import pitch_shift, pitch_shift_simple
from core.effects.time_stretch import time_stretch
from core.effects.granular import granular
from core.effects.tape_stop import tape_stop
from core.effects.buffer_freeze import buffer_freeze
from core.effects.delay import delay
from core.effects.ring_mod import ring_mod
from core.effects.filter import resonant_filter
from core.effects.ott import ott
from core.effects.vinyl import vinyl
from core.effects.datamosh import datamosh
from core.effects.shuffle import shuffle
from core.effects.volume import volume as volume_fx
from core.effects.chorus import chorus
from core.effects.distortion import distortion
from core.effects.phaser import phaser
from core.effects.tremolo import tremolo
from core.effects.utils import fade_in, fade_out

from utils.config import (
    COLORS, APP_NAME, APP_VERSION, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    AUDIO_EXTENSIONS, ALL_EXTENSIONS, load_settings, save_settings
)
from utils.translator import t, set_language, get_language

# Effect name -> dialog class (sorted alphabetically)
DIALOGS = {
    "Bitcrusher": BitcrusherDialog,
    "Buffer Freeze": BufferFreezeDialog,
    "Chorus": ChorusDialog,
    "Datamosh": DatamoshDialog,
    "Delay": DelayDialog,
    "Distortion": DistortionDialog,
    "Filter": FilterDialog,
    "Granular": GranularDialog,
    "OTT": OTTDialog,
    "Phaser": PhaserDialog,
    "Pitch Shift": PitchShiftDialog,
    "Reverse": ReverseDialog,
    "Ring Mod": RingModDialog,
    "Saturation": SaturationDialog,
    "Shuffle": ShuffleDialog,
    "Stutter": StutterDialog,
    "Tape Stop": TapeStopDialog,
    "Time Stretch": TimeStretchDialog,
    "Tremolo": TremoloDialog,
    "Vinyl": VinylDialog,
    "Volume": VolumeDialog,
}


class UndoState:
    __slots__ = ("audio", "sr", "clips", "desc")
    def __init__(self, audio, sr, clips, desc=""):
        self.audio = audio.copy() if audio is not None else None
        self.sr = sr; self.clips = clips; self.desc = desc


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} — v{APP_VERSION}")
        self.setMinimumSize(WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT)
        self.setAcceptDrops(True)

        # State
        self.audio_data: np.ndarray | None = None
        self.sample_rate: int = 44100
        self.current_filepath: str = ""
        self.project_filepath: str = ""
        self.timeline = Timeline()
        self.playback = PlaybackEngine()
        self.playback.on_playback_finished = self._on_finished
        self._undo: list[UndoState] = []
        self._redo: list[UndoState] = []
        self._unsaved = False
        self.preset_manager = PresetManager()

        # Build UI
        self._build_ui()
        self._build_menus()
        self._connect()
        self._setup_shortcuts()
        self._refresh_presets()

        # Playhead timer 30fps
        self._timer = QTimer()
        self._timer.setInterval(33)
        self._timer.timeout.connect(self._upd_playhead)
        self._timer.start()

        # Style
        self.setStyleSheet(f"""
            QMainWindow {{ background: {COLORS['bg_dark']}; }}
            QStatusBar {{ background: {COLORS['bg_medium']}; color: {COLORS['text_dim']}; font-size: 11px; }}
            QMenuBar {{ background: {COLORS['bg_medium']}; color: {COLORS['text']}; font-size: 11px; }}
            QMenuBar::item:selected {{ background: {COLORS['accent']}; }}
            QMenu {{ background: {COLORS['bg_medium']}; color: {COLORS['text']};
                border: 1px solid {COLORS['border']}; font-size: 11px; }}
            QMenu::item {{ padding: 5px 24px 5px 14px; min-width: 120px; }}
            QMenu::item:selected {{ background: {COLORS['accent']}; }}
            QMenu::separator {{ height: 1px; background: {COLORS['border']}; margin: 3px 8px; }}
            QToolTip {{ background: {COLORS['bg_medium']}; color: {COLORS['text']};
                border: 1px solid {COLORS['accent']}; padding: 6px; font-size: 11px; }}
        """)
        self.statusBar().showMessage("Ready")

    # ══════ UI Build ══════

    def _build_ui(self):
        c = QWidget(); self.setCentralWidget(c)
        mlo = QHBoxLayout(c); mlo.setContentsMargins(0, 0, 0, 0); mlo.setSpacing(0)

        # Sidebar
        self.effects_panel = EffectsPanel()
        self.effects_panel.setStyleSheet(f"background: {COLORS['bg_panel']};")
        mlo.addWidget(self.effects_panel)

        # Right area
        right = QWidget()
        rl = QVBoxLayout(right); rl.setContentsMargins(0, 0, 0, 0); rl.setSpacing(0)

        # Toolbar with undo/redo
        tb = QWidget(); tb.setFixedHeight(32)
        tb.setStyleSheet(f"background: {COLORS['bg_medium']};")
        tlo = QHBoxLayout(tb); tlo.setContentsMargins(8, 2, 8, 2); tlo.setSpacing(4)

        self.btn_undo = self._make_toolbar_btn("Undo  (Ctrl+Z)")
        self.btn_undo.setEnabled(False); self.btn_undo.clicked.connect(self._do_undo)
        tlo.addWidget(self.btn_undo)

        self.btn_redo = self._make_toolbar_btn("Redo  (Ctrl+Y)")
        self.btn_redo.setEnabled(False); self.btn_redo.clicked.connect(self._do_redo)
        tlo.addWidget(self.btn_redo)

        tlo.addSpacing(12)
        self.toolbar_info = QLabel("")
        self.toolbar_info.setStyleSheet(f"color: {COLORS['text_dim']}; font-size: 10px;")
        tlo.addWidget(self.toolbar_info); tlo.addStretch()
        rl.addWidget(tb)

        # Waveform
        self.waveform = WaveformWidget()
        rl.addWidget(self.waveform, stretch=3)

        # Timeline
        self.timeline_w = TimelineWidget(self.timeline)
        rl.addWidget(self.timeline_w, stretch=1)

        # Transport
        self.transport = TransportBar()
        rl.addWidget(self.transport)

        mlo.addWidget(right, stretch=1)

    def _make_toolbar_btn(self, text):
        b = QPushButton(text); b.setFixedHeight(26)
        b.setCursor(Qt.CursorShape.PointingHandCursor)
        b.setStyleSheet(f"""
            QPushButton {{ background: {COLORS['button_bg']}; color: {COLORS['text']};
                border: 1px solid {COLORS['border']}; border-radius: 4px;
                font-size: 10px; padding: 0 10px; }}
            QPushButton:hover {{ background: {COLORS['button_hover']}; border-color: {COLORS['accent']}; }}
            QPushButton:disabled {{ color: {COLORS['text_dim']}; background: {COLORS['bg_dark']}; }}
        """)
        return b

    def _build_menus(self):
        """Build or rebuild the entire menu bar."""
        mb = self.menuBar(); mb.clear()

        # File
        fm = mb.addMenu(t("menu.file"))
        self._menu_action(fm, t("menu.file.open"), "Ctrl+O", self._open)
        self._menu_action(fm, t("menu.file.record"), "", self._record)
        fm.addSeparator()
        self._menu_action(fm, t("menu.file.save"), "Ctrl+S", self._save)
        self._menu_action(fm, t("menu.file.save_as"), "Ctrl+Shift+S", self._save_as)
        fm.addSeparator()
        self._menu_action(fm, t("menu.file.export_wav"), "", lambda: self._export("wav"))
        self._menu_action(fm, t("menu.file.export_mp3"), "", lambda: self._export("mp3"))
        self._menu_action(fm, t("menu.file.export_flac"), "", lambda: self._export("flac"))
        fm.addSeparator()
        self._menu_action(fm, t("menu.file.quit"), "Ctrl+Q", self.close)

        # Options
        om = mb.addMenu(t("menu.options"))
        self._menu_action(om, t("menu.options.audio"), "", self._settings_audio)
        self._menu_action(om, t("menu.options.language"), "", self._settings_language)
        om.addSeparator()
        self._menu_action(om, t("menu.options.select_all"), "Ctrl+A", self._select_all)

        # Effects (grouped by category)
        efm = mb.addMenu(t("menu.effects"))

        # Basics
        for n in ["Reverse", "Volume", "Filter"]:
            self._menu_action(efm, n, "", lambda _, n=n: self._on_effect(n))
        efm.addSeparator()

        # Pitch & Time
        for n in ["Pitch Shift", "Time Stretch", "Tape Stop"]:
            self._menu_action(efm, n, "", lambda _, n=n: self._on_effect(n))
        efm.addSeparator()

        # Distortion
        for n in ["Saturation", "Distortion", "Bitcrusher"]:
            self._menu_action(efm, n, "", lambda _, n=n: self._on_effect(n))
        efm.addSeparator()

        # Modulation
        for n in ["Chorus", "Phaser", "Tremolo", "Ring Mod"]:
            self._menu_action(efm, n, "", lambda _, n=n: self._on_effect(n))
        efm.addSeparator()

        # Space & Texture
        for n in ["Delay", "Vinyl", "OTT"]:
            self._menu_action(efm, n, "", lambda _, n=n: self._on_effect(n))
        efm.addSeparator()

        # Glitch
        for n in ["Stutter", "Granular", "Shuffle", "Buffer Freeze", "Datamosh"]:
            self._menu_action(efm, n, "", lambda _, n=n: self._on_effect(n))
        efm.addSeparator()

        self._menu_action(efm, t("menu.effects.catalog"), "", self._catalog)

        # Help
        hm = mb.addMenu(t("menu.help"))
        self._menu_action(hm, t("menu.help.about"), "", lambda: AboutDialog(self).exec())

    def _menu_action(self, menu, text, shortcut, slot) -> QAction:
        a = menu.addAction(text)
        if shortcut: a.setShortcut(shortcut)
        a.triggered.connect(slot); return a

    def _setup_shortcuts(self):
        for key, slot in [
            (Qt.Key.Key_Space, self._toggle_play),
            (Qt.Key.Key_Escape, self._deselect),
        ]:
            s = QShortcut(QKeySequence(key), self)
            s.setContext(Qt.ShortcutContext.WindowShortcut)
            s.activated.connect(slot)
        for seq, slot in [("Ctrl+Z", self._do_undo), ("Ctrl+Y", self._do_redo)]:
            s = QShortcut(QKeySequence(seq), self)
            s.setContext(Qt.ShortcutContext.WindowShortcut)
            s.activated.connect(slot)

    def _connect(self):
        self.transport.play_clicked.connect(self._play)
        self.transport.pause_clicked.connect(self._pause)
        self.transport.stop_clicked.connect(self._stop)
        self.transport.volume_changed.connect(self.playback.set_volume)
        self.waveform.position_clicked.connect(self._seek)
        self.waveform.selection_changed.connect(self._on_sel)
        self.effects_panel.effect_clicked.connect(self._on_effect)
        self.effects_panel.catalog_clicked.connect(self._catalog)
        self.effects_panel.preset_clicked.connect(self._on_preset)
        self.effects_panel.preset_new_clicked.connect(self._new_preset)
        self.effects_panel.preset_manage_clicked.connect(self._manage_presets)
        self.timeline_w.clip_selected.connect(self._on_clip_sel)
        self.timeline_w.split_requested.connect(self._split_clip)
        self.timeline_w.duplicate_requested.connect(self._dup_clip)
        self.timeline_w.delete_requested.connect(self._del_clip)
        self.timeline_w.fade_in_requested.connect(self._fi_clip)
        self.timeline_w.fade_out_requested.connect(self._fo_clip)
        self.timeline_w.clips_reordered.connect(self._on_reorder)

    def _update_undo_labels(self):
        hu, hr = bool(self._undo), bool(self._redo)
        self.btn_undo.setEnabled(hu); self.btn_redo.setEnabled(hr)
        if hu:
            self.btn_undo.setText(f"Undo: {self._undo[-1].desc}  (Ctrl+Z)")
            self.toolbar_info.setText(f"{len(self._undo)} action(s)")
        else:
            self.btn_undo.setText("Undo  (Ctrl+Z)")
            self.toolbar_info.setText("")
        self.btn_redo.setText("Redo  (Ctrl+Y)")

    # ══════ Playback ══════

    def _toggle_play(self):
        if self.audio_data is None: return
        (self._pause if self.playback.is_playing else self._play)()

    def _play(self):
        if self.audio_data is None: return
        s, e = self._sel_range()
        if s is not None:
            self.playback.set_loop(s, e, looping=True)
            if not self.playback.is_paused:
                self.playback.play(start_pos=s)
            else:
                self.playback.play()
        else:
            self.playback.set_loop(None, None, looping=False)
            self.playback.play()
        self.transport.set_playing(True)

    def _pause(self):
        self.playback.pause(); self.transport.set_playing(False)

    def _stop(self):
        self.playback.stop(); self.transport.set_playing(False)
        self.waveform.set_playhead(0)
        self.timeline_w.set_playhead(0, self.sample_rate)
        if self.audio_data is not None:
            self.transport.set_time("00:00.00", format_time(get_duration(self.audio_data, self.sample_rate)))

    def _seek(self, pos):
        self.playback.seek(pos); self.waveform.set_playhead(pos)

    def _on_sel(self, s, e):
        dur = format_time(abs(e - s) / self.sample_rate)
        self.transport.set_selection_info(f"Sel: {dur}")
        # Deselect any timeline clip
        self.timeline_w._selected_id = None
        self.timeline_w.update()
        # Move playhead to selection start
        start = min(s, e)
        self.playback.seek(start)
        self.waveform.set_playhead(start)
        self.timeline_w.set_playhead(start, self.sample_rate)

    def _on_finished(self):
        QTimer.singleShot(0, lambda: self.transport.set_playing(False))

    def _upd_playhead(self):
        if self.playback.is_playing and self.audio_data is not None:
            pos = self.playback.position
            self.waveform.set_playhead(pos)
            self.timeline_w.set_playhead(pos, self.sample_rate)
            self.transport.set_time(
                format_time(pos / self.sample_rate),
                format_time(get_duration(self.audio_data, self.sample_rate)))

    def _sel_range(self):
        s, e = self.waveform.selection_start, self.waveform.selection_end
        if s is not None and e is not None and s != e:
            return min(s, e), max(s, e)
        return None, None

    def _deselect(self):
        self.waveform.set_selection(None, None)
        self.waveform.set_clip_highlight(None, None)
        self.transport.set_selection_info("")

    # ══════ Open ══════

    def _open(self):
        exts_list = " ".join(["*" + e for e in sorted(ALL_EXTENSIONS)])
        fp, _ = QFileDialog.getOpenFileName(
            self, t("menu.file.open"), "",
            f"Audio & Projects ({exts_list});;All files (*)")
        if not fp:
            return
        ext = os.path.splitext(fp)[1].lower()
        if ext == ".gspi":
            self._load_gspi(fp)
        elif ext in AUDIO_EXTENSIONS:
            self._load_audio(fp)

    def _load_audio(self, fp):
        try:
            self._stop()
            data, sr = load_audio(fp)
            st = ensure_stereo(data)
            name = os.path.splitext(os.path.basename(fp))[0]

            if self.audio_data is None:
                self.audio_data, self.sample_rate = st, sr
                self.current_filepath = fp
                self.timeline.clear()
                self.timeline.add_clip(st, sr, name=name, position=0)
            else:
                self._push_undo("Import")
                self.timeline.add_clip(st, sr, name=name)
                self._rebuild_audio()

            self._refresh_all()
            self._undo.clear(); self._redo.clear(); self._update_undo_labels()
            self._unsaved = True
            self.setWindowTitle(f"{APP_NAME} — {os.path.basename(fp)}")
            self.statusBar().showMessage(f"Loaded: {os.path.basename(fp)}")
        except Exception as e:
            QMessageBox.critical(self, APP_NAME, str(e))

    def _load_gspi(self, fp):
        try:
            self._stop()
            tl, sr, src = load_project(fp)
            self.timeline, self.sample_rate = tl, sr
            self.current_filepath = src
            self.project_filepath = fp
            self._rebuild_audio()
            self._undo.clear(); self._redo.clear(); self._update_undo_labels()
            self._unsaved = False
            self.setWindowTitle(f"{APP_NAME} — {os.path.splitext(os.path.basename(fp))[0]}")
            self.statusBar().showMessage(f"Project: {os.path.basename(fp)}")
        except Exception as e:
            QMessageBox.critical(self, APP_NAME, str(e))

    # ══════ Save ══════

    def _save(self):
        if not self.timeline.clips:
            QMessageBox.warning(self, APP_NAME, t("error.empty_timeline")); return
        if self.project_filepath:
            self._do_save(self.project_filepath)
        else:
            self._save_as()

    def _save_as(self):
        if not self.timeline.clips:
            QMessageBox.warning(self, APP_NAME, t("error.empty_timeline")); return
        fp, _ = QFileDialog.getSaveFileName(
            self, t("menu.file.save_as"), "project.gspi", "Glitch Maker (*.gspi)")
        if fp:
            if not fp.endswith(".gspi"):
                fp += ".gspi"
            self._do_save(fp)

    def _do_save(self, fp):
        try:
            save_project(fp, self.timeline, self.sample_rate, self.current_filepath)
            self.project_filepath = fp
            self._unsaved = False
            self.statusBar().showMessage(f"Saved: {os.path.basename(fp)}")
        except Exception as e:
            QMessageBox.critical(self, APP_NAME, str(e))

    # ══════ Export ══════

    def _export(self, fmt):
        if self.audio_data is None:
            QMessageBox.warning(self, APP_NAME, t("error.no_audio")); return
        fmap = {"wav": "WAV (*.wav)", "mp3": "MP3 (*.mp3)", "flac": "FLAC (*.flac)"}
        fp, _ = QFileDialog.getSaveFileName(self, "Export", f"export.{fmt}", fmap.get(fmt, ""))
        if fp:
            try:
                export_audio(self.audio_data, self.sample_rate, fp, fmt)
                self.statusBar().showMessage(f"Exported: {fp}")
            except Exception as e:
                QMessageBox.critical(self, APP_NAME, str(e))

    # ══════ Refresh ══════

    def _refresh_all(self):
        self.timeline_w.timeline = self.timeline
        self.timeline_w.sample_rate = self.sample_rate
        self.timeline_w.update()
        if self.audio_data is not None:
            self.waveform.set_audio(self.audio_data, self.sample_rate)
            self.playback.load(self.audio_data, self.sample_rate)
            self.transport.set_time("00:00.00",
                                    format_time(get_duration(self.audio_data, self.sample_rate)))
        self.transport.set_selection_info("")

    def _rebuild_audio(self):
        rendered, sr = self.timeline.render()
        if len(rendered) > 0:
            self.audio_data, self.sample_rate = rendered, sr
        self._refresh_all()

    # ══════ Clip selection → waveform highlight ══════

    def _on_clip_sel(self, clip_id):
        for c in self.timeline.clips:
            if c.id == clip_id:
                self.waveform.set_clip_highlight(c.position, c.end_position)
                self.waveform.set_selection(c.position, c.end_position)
                self.waveform.selection_changed.emit(c.position, c.end_position)
                return
        self.waveform.set_clip_highlight(None, None)

    # ══════ Effects (modify in-place) ══════

    def _on_effect(self, name):
        if self.audio_data is None:
            QMessageBox.warning(self, APP_NAME, t("error.no_audio")); return
        dlg = DIALOGS.get(name)
        if not dlg:
            return
        d = dlg(self)
        if d.exec() != d.DialogCode.Accepted:
            return
        self._push_undo(name)
        self._apply_effect(name, d.get_params())

    def _apply_effect(self, name, params):
        try:
            s, e = self._sel_range()
            if s is None:
                s, e = 0, len(self.audio_data)
            segment = self.audio_data[s:e].copy()
            sl = len(segment)
            if sl == 0:
                return

            mod = self._run_effect(name, segment, sl, self.sample_rate, params)
            if mod is None:
                return
            mod = mod.astype(np.float32)

            before = self.audio_data[:s]
            after = self.audio_data[e:]
            self.audio_data = np.concatenate(
                [p for p in [before, mod, after] if len(p) > 0], axis=0
            ).astype(np.float32)

            self._update_clips_from_audio()
            self._refresh_all()
            self._unsaved = True
            self.statusBar().showMessage(f"Applied: {name}")
        except Exception as ex:
            QMessageBox.critical(self, APP_NAME, f"{name}: {ex}")
            if self._undo:
                self._do_undo()

    def _update_clips_from_audio(self):
        if not self.timeline.clips:
            return
        total = len(self.audio_data)
        if len(self.timeline.clips) == 1:
            c = self.timeline.clips[0]
            c.audio_data = ensure_stereo(self.audio_data)
            c.position = 0
            return
        old_total = sum(c.duration_samples for c in self.timeline.clips)
        if old_total == 0:
            return
        ratio = total / old_total
        pos = 0
        for c in self.timeline.clips:
            new_len = int(c.duration_samples * ratio)
            new_len = min(new_len, total - pos)
            if new_len > 0:
                c.audio_data = ensure_stereo(self.audio_data[pos:pos + new_len])
            c.position = pos
            pos += new_len
        if pos < total and self.timeline.clips:
            last = self.timeline.clips[-1]
            extra = ensure_stereo(self.audio_data[pos:total])
            last.audio_data = np.concatenate([last.audio_data, extra], axis=0)

    def _run_effect(self, name, seg, sl, sr, p):
        """Run an effect with param translation from dialog keys → function keys."""
        try:
            if name == "Stutter":
                # Dialog: repeats, size_ms  →  Func: repeats, decay, stutter_mode
                return stutter(seg, 0, sl,
                               repeats=p.get("repeats", 4),
                               decay=p.get("decay", 0.0),
                               stutter_mode=p.get("stutter_mode", "normal"))

            if name == "Bitcrusher":
                return bitcrush(seg, 0, sl,
                                bit_depth=p.get("bit_depth", 8),
                                downsample=p.get("downsample", 4))

            if name == "Saturation":
                tp = p.get("type", "soft")
                drive = p.get("drive", 3.0)
                if tp == "hard":
                    return hard_clip(seg, 0, sl, threshold=max(0.01, 1.0 / drive))
                elif tp == "overdrive":
                    return overdrive(seg, 0, sl, gain=drive, tone=0.5)
                else:
                    return soft_clip(seg, 0, sl, drive=drive)

            if name == "Reverse":
                return reverse(seg, 0, sl)

            if name == "Pitch Shift":
                simple = p.get("simple", False)
                semi = p.get("semitones", 0)
                if simple:
                    return pitch_shift_simple(seg, 0, sl, semitones=semi)
                return pitch_shift(seg, 0, sl, semitones=semi, sr=sr)

            if name == "Time Stretch":
                return time_stretch(seg, 0, sl, factor=p.get("factor", 1.0))

            if name == "Granular":
                # Dialog: grain_ms, density, chaos  →  Func: grain_size_ms, density, randomize
                return granular(seg, 0, sl, sr=sr,
                                grain_size_ms=p.get("grain_ms", p.get("grain_size_ms", 50)),
                                density=p.get("density", 1.0),
                                randomize=p.get("chaos", p.get("randomize", 0.5)))

            if name == "Tape Stop":
                # Dialog: duration_ms  →  Func: duration_pct
                dur_ms = p.get("duration_ms", 1500)
                dur_pct = p.get("duration_pct", dur_ms / 3000.0)
                return tape_stop(seg, 0, sl, duration_pct=min(1.0, max(0.05, dur_pct)), sr=sr)

            if name == "Buffer Freeze":
                # Dialog: buffer_ms  →  Func: grain_ms, repeats
                return buffer_freeze(seg, 0, sl, sr=sr,
                                     grain_ms=p.get("buffer_ms", p.get("grain_ms", 80)),
                                     repeats=p.get("repeats", 0))

            if name == "Delay":
                return delay(seg, 0, sl, sr=sr,
                             delay_ms=p.get("delay_ms", 200),
                             feedback=p.get("feedback", 0.6),
                             mix=p.get("mix", 0.5))

            if name == "Ring Mod":
                # Dialog: frequency  →  Func: freq
                return ring_mod(seg, 0, sl, sr=sr,
                                freq=p.get("frequency", p.get("freq", 440)),
                                mix=p.get("mix", 0.7))

            if name == "Filter":
                # Dialog: cutoff_hz  →  Func: cutoff
                return resonant_filter(seg, 0, sl, sr=sr,
                                       filter_type=p.get("filter_type", "lowpass"),
                                       cutoff=p.get("cutoff_hz", p.get("cutoff", 2000)),
                                       resonance=p.get("resonance", 1.0),
                                       sweep=p.get("sweep", False))

            if name == "OTT":
                return ott(seg, 0, sl, sr=sr, depth=p.get("depth", 0.7))

            if name == "Vinyl":
                # Dialog: amount  →  Func: crackle, noise, wow
                amt = p.get("amount", None)
                if amt is not None:
                    return vinyl(seg, 0, sl, sr=sr,
                                 crackle=amt, noise=amt * 0.6, wow=amt * 0.4)
                return vinyl(seg, 0, sl, sr=sr,
                             crackle=p.get("crackle", 0.5),
                             noise=p.get("noise", 0.3),
                             wow=p.get("wow", 0.2))

            if name == "Datamosh":
                # Dialog: chaos  →  Func: intensity
                return datamosh(seg, 0, sl,
                                intensity=p.get("chaos", p.get("intensity", 0.5)),
                                block_size=p.get("block_size", 512),
                                mode=p.get("mode", "swap"))

            if name == "Shuffle":
                # Dialog: num_slices  →  Func: slices
                return shuffle(seg, 0, sl,
                               slices=p.get("num_slices", p.get("slices", 8)),
                               mode=p.get("mode", "random"))

            if name == "Volume":
                return volume_fx(seg, 0, sl, gain_pct=p.get("gain_pct", 100))

            if name == "Chorus":
                return chorus(seg, 0, sl, sr=sr,
                              depth_ms=p.get("depth_ms", 5),
                              rate_hz=p.get("rate_hz", 1.5),
                              mix=p.get("mix", 0.5),
                              voices=p.get("voices", 2))

            if name == "Distortion":
                return distortion(seg, 0, sl,
                                  drive=p.get("drive", 5),
                                  tone=p.get("tone", 0.5),
                                  mode=p.get("mode", "tube"))

            if name == "Phaser":
                return phaser(seg, 0, sl, sr=sr,
                              rate_hz=p.get("rate_hz", 0.5),
                              depth=p.get("depth", 0.7),
                              stages=p.get("stages", 4),
                              mix=p.get("mix", 0.7))

            if name == "Tremolo":
                return tremolo(seg, 0, sl, sr=sr,
                               rate_hz=p.get("rate_hz", 5),
                               depth=p.get("depth", 0.7),
                               shape=p.get("shape", "sine"))

        except Exception as ex:
            print(f"[effect] {name} error: {ex}")
            self.statusBar().showMessage(f"Error: {name}: {ex}")
        return None

    # ══════ Presets ══════

    def _refresh_presets(self):
        all_presets = self.preset_manager.get_all_presets()
        tag_map = {}
        for tag in self.preset_manager.get_all_tags():
            presets = self.preset_manager.get_presets_by_tag(tag)
            if presets:
                tag_map[tag] = presets
        self.effects_panel.set_presets(tag_map, all_presets)

    def _on_preset(self, name):
        if self.audio_data is None:
            QMessageBox.warning(self, APP_NAME, t("error.no_audio")); return
        s, e = self._sel_range()
        if s is None:
            QMessageBox.warning(self, APP_NAME, t("preset.need_selection")); return
        preset = self.preset_manager.get_preset(name)
        if not preset:
            return
        self._push_undo(f"Preset: {name}")
        for eff in preset["effects"]:
            try:
                segment = self.audio_data[s:e].copy()
                sl = len(segment)
                if sl == 0:
                    break
                eff_name = eff["name"]
                if eff_name == "Filtre":
                    eff_name = "Filter"
                mod = self._run_effect(eff_name, segment, sl, self.sample_rate, dict(eff["params"]))
                if mod is not None:
                    mod = mod.astype(np.float32)
                    before, after = self.audio_data[:s], self.audio_data[e:]
                    self.audio_data = np.concatenate(
                        [p for p in [before, mod, after] if len(p) > 0], axis=0
                    ).astype(np.float32)
                    e = s + len(mod)
            except Exception as ex:
                self.statusBar().showMessage(f"Error {eff['name']}: {ex}")
                break
        self._update_clips_from_audio()
        self._refresh_all()
        self._unsaved = True
        self.statusBar().showMessage(f"Preset applied: {name}")

    def _new_preset(self):
        tags = self.preset_manager.get_all_tags()
        dlg = PresetCreateDialog(tags, self, preset_manager=self.preset_manager)
        if dlg.exec() == dlg.DialogCode.Accepted and dlg.result_preset:
            r = dlg.result_preset
            self.preset_manager.add_preset(r["name"], r["description"], r["tags"], r["effects"])
            self._refresh_presets()

    def _manage_presets(self):
        dlg = PresetManageDialog(self.preset_manager, self)
        dlg.exec()
        if dlg.deleted:
            self._refresh_presets()

    # ══════ Timeline ops ══════

    def _on_reorder(self):
        try:
            self._push_undo("Reorder")
            self._rebuild_audio()
            self._unsaved = True
        except Exception as e:
            print(f"[reorder] error: {e}")
            self.statusBar().showMessage(f"Reorder error: {e}")

    def _split_clip(self, cid, pos):
        clip = self._find_clip(cid)
        if not clip or pos <= 0 or pos >= clip.duration_samples:
            return
        self._push_undo("Cut")
        idx = self.timeline.clips.index(clip)
        a, b = clip.audio_data[:pos].copy(), clip.audio_data[pos:].copy()
        self.timeline.clips.remove(clip)
        ca = AudioClip(name=f"{clip.name} (A)", audio_data=a, sample_rate=clip.sample_rate,
                       position=clip.position, color=clip.color)
        cb = AudioClip(name=f"{clip.name} (B)", audio_data=b, sample_rate=clip.sample_rate,
                       position=clip.position + len(a), color="#16c79a")
        self.timeline.clips.insert(idx, cb)
        self.timeline.clips.insert(idx, ca)
        self._rebuild_audio(); self._unsaved = True

    def _dup_clip(self, cid):
        clip = self._find_clip(cid)
        if not clip:
            return
        self._push_undo("Duplicate")
        end = max(c.end_position for c in self.timeline.clips)
        nc = AudioClip(name=f"{clip.name} (copy)", audio_data=clip.audio_data.copy(),
                       sample_rate=clip.sample_rate, position=end, color=clip.color)
        self.timeline.clips.append(nc)
        self._rebuild_audio(); self._unsaved = True

    def _del_clip(self, cid):
        clip = self._find_clip(cid)
        if not clip or len(self.timeline.clips) <= 1:
            QMessageBox.warning(self, APP_NAME, t("error.cant_delete")); return
        self._push_undo("Delete")
        self.timeline.clips.remove(clip)
        pos = 0
        for c in self.timeline.clips:
            c.position = pos
            pos += c.duration_samples
        self._rebuild_audio(); self._unsaved = True

    def _fi_clip(self, cid):
        clip = self._find_clip(cid)
        if not clip:
            return
        self._push_undo("Fade In")
        n = min(int(0.5 * clip.sample_rate), clip.duration_samples // 2)
        clip.audio_data = fade_in(clip.audio_data, n)
        self._rebuild_audio(); self._unsaved = True

    def _fo_clip(self, cid):
        clip = self._find_clip(cid)
        if not clip:
            return
        self._push_undo("Fade Out")
        n = min(int(0.5 * clip.sample_rate), clip.duration_samples // 2)
        clip.audio_data = fade_out(clip.audio_data, n)
        self._rebuild_audio(); self._unsaved = True

    def _find_clip(self, cid):
        for c in self.timeline.clips:
            if c.id == cid:
                return c
        return None

    # ══════ Undo / Redo ══════

    def _push_undo(self, desc):
        if self.audio_data is None:
            return
        clips = [(c.name, c.audio_data.copy(), c.position, c.color) for c in self.timeline.clips]
        self._undo.append(UndoState(self.audio_data, self.sample_rate, clips, desc))
        if len(self._undo) > 30:
            self._undo.pop(0)
        self._redo.clear()
        self._update_undo_labels()

    def _do_undo(self):
        if not self._undo:
            return
        cn = [(c.name, c.audio_data.copy(), c.position, c.color) for c in self.timeline.clips]
        self._redo.append(UndoState(self.audio_data, self.sample_rate, cn, ""))
        self._restore(self._undo.pop())
        self.statusBar().showMessage("Undo")
        self._update_undo_labels()

    def _do_redo(self):
        if not self._redo:
            return
        cn = [(c.name, c.audio_data.copy(), c.position, c.color) for c in self.timeline.clips]
        self._undo.append(UndoState(self.audio_data, self.sample_rate, cn, ""))
        self._restore(self._redo.pop())
        self.statusBar().showMessage("Redo")
        self._update_undo_labels()

    def _restore(self, state):
        self._stop()
        self.audio_data = state.audio.copy() if state.audio is not None else None
        self.sample_rate = state.sr
        self.timeline.clear()
        for name, data, pos, color in state.clips:
            c = AudioClip(name=name, audio_data=data.copy(), sample_rate=state.sr,
                          position=pos, color=color)
            self.timeline.clips.append(c)
        self.timeline.sample_rate = state.sr
        self._refresh_all()

    # ══════ Settings ══════

    def _settings_audio(self):
        dlg = SettingsDialog(self.playback.output_device, self.playback.input_device, self)
        if dlg.exec() == dlg.DialogCode.Accepted:
            self.playback.set_output_device(dlg.selected_output)
            self.playback.set_input_device(dlg.selected_input)
            self.statusBar().showMessage("Audio devices updated")

    def _settings_language(self):
        from PyQt6.QtWidgets import QInputDialog
        langs = ["English", "Français"]
        codes = ["en", "fr"]
        cur_idx = codes.index(get_language()) if get_language() in codes else 0
        choice, ok = QInputDialog.getItem(
            self, "Language", "Select language:", langs, cur_idx, False)
        if ok:
            new_lang = codes[langs.index(choice)]
            if new_lang != get_language():
                set_language(new_lang)
                settings = load_settings()
                settings["language"] = new_lang
                save_settings(settings)
                self._build_menus()
                self._update_undo_labels()
                self.statusBar().showMessage(t("status.lang_changed"))

    # ══════ Misc ══════

    def _record(self):
        d = RecordDialog(input_device=self.playback.input_device, parent=self)
        d.recording_done.connect(self._on_rec)
        d.exec()

    def _on_rec(self, data, sr):
        st = ensure_stereo(data)
        if self.audio_data is None:
            self.audio_data, self.sample_rate = st, sr
        else:
            self._push_undo("Rec")
            self.audio_data = np.concatenate([self.audio_data, st], axis=0).astype(np.float32)
        self.timeline.add_clip(st, sr, name=f"Rec {len(self.timeline.clips) + 1}")
        self._refresh_all()
        self._unsaved = True

    def _select_all(self):
        if self.audio_data is not None:
            self.waveform.set_selection(0, len(self.audio_data))
            self.waveform.selection_changed.emit(0, len(self.audio_data))

    def _catalog(self):
        CatalogDialog(self).exec()

    # ══════ Drag & Drop ══════

    def dragEnterEvent(self, e: QDragEnterEvent):
        if e.mimeData().hasUrls():
            for u in e.mimeData().urls():
                ext = os.path.splitext(u.toLocalFile())[1].lower()
                if ext in ALL_EXTENSIONS:
                    e.acceptProposedAction()
                    return
        e.ignore()

    def dropEvent(self, e: QDropEvent):
        for u in e.mimeData().urls():
            fp = u.toLocalFile()
            ext = os.path.splitext(fp)[1].lower()
            if ext == ".gspi":
                self._load_gspi(fp)
            elif ext in AUDIO_EXTENSIONS:
                self._load_audio(fp)
            return

    # ══════ Close ══════

    def closeEvent(self, e):
        if self._unsaved and self.audio_data is not None:
            r = QMessageBox.question(
                self, APP_NAME, "Unsaved changes. Save project?",
                QMessageBox.StandardButton.Save | QMessageBox.StandardButton.Discard | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save)
            if r == QMessageBox.StandardButton.Save:
                self._save()
                e.accept()
            elif r == QMessageBox.StandardButton.Discard:
                e.accept()
            else:
                e.ignore()
                return
        self.playback.cleanup()
        self._timer.stop()
        e.accept()
