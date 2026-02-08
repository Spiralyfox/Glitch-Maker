"""Playback engine — always-on stream for zero latency. device=None = system default."""
import numpy as np
import sounddevice as sd

class PlaybackEngine:
    def __init__(self):
        self.audio_data: np.ndarray | None = None
        self.sample_rate: int = 44100
        self.position: int = 0
        self.is_playing: bool = False
        self.is_paused: bool = False
        self.volume: float = 0.8
        self.output_device = None  # None = system default
        self.input_device = None   # None = system default
        self._stream = None
        self.on_playback_finished = None
        self.loop_start: int | None = None
        self.loop_end: int | None = None
        self.looping: bool = False

    def load(self, audio_data: np.ndarray, sr: int):
        self.audio_data = audio_data.astype(np.float32) if audio_data is not None else None
        self.sample_rate = sr
        self.position = 0
        self.is_playing = False
        self.is_paused = False
        self._ensure_stream()

    def _ensure_stream(self):
        if self._stream is not None:
            try: self._stream.close()
            except Exception: pass
        if self.audio_data is None or self.sample_rate <= 0: return
        ch = self.audio_data.shape[1] if self.audio_data.ndim > 1 else 1
        try:
            self._stream = sd.OutputStream(
                samplerate=self.sample_rate, channels=ch, dtype="float32",
                callback=self._callback, blocksize=512,
                device=self.output_device)  # None = system default
            self._stream.start()
        except Exception as e:
            print(f"[playback] stream error: {e}")
            self._stream = None

    def _callback(self, outdata, frames, time_info, status):
        if not self.is_playing or self.audio_data is None:
            outdata[:] = 0; return
        n = len(self.audio_data)
        pos = self.position
        end = min(pos + frames, n)
        valid = end - pos
        if valid <= 0:
            outdata[:] = 0
            if self.looping and self.loop_start is not None:
                self.position = self.loop_start
            else:
                self.is_playing = False
                if self.on_playback_finished: self.on_playback_finished()
            return
        data = self.audio_data[pos:end]
        if data.ndim == 1: data = data.reshape(-1, 1)
        if data.shape[1] < outdata.shape[1]:
            data = np.column_stack([data] * outdata.shape[1])
        elif data.shape[1] > outdata.shape[1]:
            data = data[:, :outdata.shape[1]]
        outdata[:valid] = data[:valid] * self.volume
        if valid < frames: outdata[valid:] = 0
        self.position = end
        # Loop check
        if self.looping and self.loop_end is not None and self.position >= self.loop_end:
            self.position = self.loop_start if self.loop_start is not None else 0

    def play(self, start_pos=None):
        if self.audio_data is None: return
        if start_pos is not None: self.position = start_pos
        self.is_playing = True; self.is_paused = False
        if self._stream is None: self._ensure_stream()

    def pause(self):
        self.is_playing = False; self.is_paused = True

    def stop(self):
        self.is_playing = False; self.is_paused = False; self.position = 0

    def seek(self, pos):
        self.position = max(0, min(pos, len(self.audio_data) - 1 if self.audio_data is not None else 0))

    def set_volume(self, v): self.volume = max(0.0, min(1.0, v))

    def set_loop(self, start, end, looping=False):
        self.loop_start = start; self.loop_end = end; self.looping = looping

    def set_output_device(self, device_idx):
        self.output_device = device_idx
        if self.audio_data is not None: self._ensure_stream()

    def set_input_device(self, device_idx):
        self.input_device = device_idx

    def cleanup(self):
        self.is_playing = False
        if self._stream:
            try: self._stream.close()
            except Exception: pass
            self._stream = None
