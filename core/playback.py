"""Moteur de lecture audio — stream low-latency avec support metronome."""
import logging
import threading
import numpy as np
import sounddevice as sd
from core.metronome import Metronome

log = logging.getLogger(__name__)


class PlaybackEngine:
    """Lecture audio temps reel via OutputStream sounddevice.
    Blocksize 256 (~6ms latence). Thread-safe via Lock sur position/is_playing.
    Supporte boucle, volume, metronome."""

    def __init__(self):
        """Initialise l'engine sans audio charge."""
        self._lock = threading.Lock()
        self.audio_data: np.ndarray | None = None
        self.sample_rate: int = 44100
        self.position: int = 0
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.volume: float = 0.8
        self.output_device = None
        self.input_device = None
        self._stream = None
        self._stream_sr = 0
        self._stream_ch = 0
        self.on_playback_finished = None
        self.loop_start: int | None = None
        self.loop_end: int | None = None
        self.looping: bool = False
        self.metronome = Metronome()

    def load(self, audio_data: np.ndarray, sr: int):
        """Charge un tableau numpy audio et prepare le stream de sortie."""
        if audio_data is not None and audio_data.dtype != np.float32:
            audio_data = audio_data.astype(np.float32)
        with self._lock:
            self.audio_data = audio_data
            self.sample_rate = sr
            self.position = 0
            self.is_playing = False
            self.is_paused = False
        self.metronome.set_sr(sr)
        ch = audio_data.shape[1] if audio_data is not None and audio_data.ndim > 1 else 1
        if sr != self._stream_sr or ch != self._stream_ch or self._stream is None:
            self._ensure_stream()

    def _ensure_stream(self):
        """Cree ou recreee le stream de sortie avec les bons parametres."""
        if self._stream is not None:
            try:
                self._stream.close()
            except Exception as e:
                log.debug("stream close: %s", e)
            self._stream = None
        with self._lock:
            if self.audio_data is None or self.sample_rate <= 0:
                self._stream_sr = 0; self._stream_ch = 0; return
            ch = self.audio_data.shape[1] if self.audio_data.ndim > 1 else 1
        try:
            self._stream = sd.OutputStream(
                samplerate=self.sample_rate, channels=ch, dtype="float32",
                callback=self._callback, blocksize=256, latency='low',
                device=self.output_device)
            self._stream.start()
            self._stream_sr = self.sample_rate
            self._stream_ch = ch
        except Exception as e:
            log.error("stream error: %s", e)
            self._stream = None; self._stream_sr = 0; self._stream_ch = 0

    def _callback(self, outdata, frames, time_info, status):
        """Callback audio (thread audio) — remplit le buffer, applique volume, metronome."""
        with self._lock:
            playing = self.is_playing
            audio = self.audio_data
        if not playing or audio is None:
            outdata[:] = 0; return
        n = len(audio)
        pos = self.position
        end = min(pos + frames, n)
        valid = end - pos
        if valid <= 0:
            outdata[:] = 0
            if self.looping and self.loop_start is not None:
                self.position = self.loop_start
            else:
                with self._lock:
                    self.is_playing = False
                if self.on_playback_finished:
                    self.on_playback_finished()
            return
        data = audio[pos:end]
        if data.ndim == 1: data = data.reshape(-1, 1)
        if data.shape[1] < outdata.shape[1]:
            data = np.column_stack([data] * outdata.shape[1])
        elif data.shape[1] > outdata.shape[1]:
            data = data[:, :outdata.shape[1]]
        outdata[:valid] = data[:valid] * self.volume
        if valid < frames: outdata[valid:] = 0
        self.metronome.mix_into(outdata, pos, frames)
        self.position = end
        if self.looping and self.loop_end is not None and self.position >= self.loop_end:
            self.position = self.loop_start if self.loop_start is not None else 0

    def play(self, start_pos=None):
        """Demarre la lecture depuis start_pos (ou la position actuelle)."""
        if self.audio_data is None: return
        with self._lock:
            if start_pos is not None: self.position = start_pos
            self.is_playing = True; self.is_paused = False
        if self._stream is None: self._ensure_stream()

    def pause(self):
        """Met en pause la lecture."""
        with self._lock:
            self.is_playing = False; self.is_paused = True

    def stop(self):
        """Arrete la lecture et revient au debut."""
        with self._lock:
            self.is_playing = False; self.is_paused = False; self.position = 0

    def seek(self, pos):
        """Deplace la tete de lecture a la position donnee (en samples)."""
        with self._lock:
            mx = len(self.audio_data) - 1 if self.audio_data is not None else 0
            self.position = max(0, min(pos, mx))

    def set_volume(self, v):
        """Change le volume de sortie (0.0-1.0)."""
        self.volume = max(0.0, min(1.0, v))

    def set_loop(self, start, end, looping=False):
        """Configure la boucle de lecture (debut, fin en samples)."""
        self.loop_start = start; self.loop_end = end; self.looping = looping

    def set_output_device(self, device_idx):
        """Change le peripherique de sortie audio et recreee le stream."""
        self.output_device = device_idx
        if self.audio_data is not None: self._ensure_stream()

    def set_input_device(self, device_idx):
        """Change le peripherique d'entree (pour enregistrement)."""
        self.input_device = device_idx

    def cleanup(self):
        """Ferme le stream audio proprement (appele a la fermeture)."""
        with self._lock:
            self.is_playing = False
        if self._stream:
            try:
                self._stream.close()
            except Exception as e:
                log.debug("cleanup: %s", e)
            self._stream = None

    def suspend_stream(self):
        """Suspend le stream (pour laisser sd.play faire la preview)."""
        with self._lock:
            self.is_playing = False
        if self._stream:
            try:
                self._stream.close()
            except Exception as e:
                log.debug("suspend: %s", e)
            self._stream = None; self._stream_sr = 0; self._stream_ch = 0

    def resume_stream(self):
        """Restaure le stream apres une preview."""
        if self.audio_data is not None and self._stream is None:
            self._ensure_stream()
