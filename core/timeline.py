"""
Timeline model — manages AudioClip instances in sequence.
"""

import uuid
import numpy as np
from dataclasses import dataclass, field


@dataclass
class AudioClip:
    """A single audio clip in the timeline."""
    name: str
    audio_data: np.ndarray
    sample_rate: int = 44100
    position: int = 0       # sample offset in timeline
    color: str = "#533483"
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])

    @property
    def duration_samples(self) -> int:
        return len(self.audio_data) if self.audio_data is not None else 0

    @property
    def duration_seconds(self) -> float:
        return self.duration_samples / self.sample_rate if self.sample_rate > 0 else 0.0

    @property
    def end_position(self) -> int:
        return self.position + self.duration_samples


class Timeline:
    """Ordered list of audio clips. Renders to a single stereo buffer."""

    def __init__(self):
        self.clips: list[AudioClip] = []
        self.sample_rate: int = 44100

    def clear(self):
        self.clips.clear()

    def add_clip(self, audio_data: np.ndarray, sr: int,
                 name: str = "Clip", position: int | None = None,
                 color: str = "#533483"):
        """Add a clip. If position is None, append after last clip."""
        if position is None:
            position = max((c.end_position for c in self.clips), default=0)
        clip = AudioClip(
            name=name, audio_data=audio_data.copy(),
            sample_rate=sr, position=position, color=color
        )
        self.clips.append(clip)
        self.sample_rate = sr
        return clip

    def render(self) -> tuple[np.ndarray, int]:
        """Render all clips into a single stereo float32 buffer."""
        if not self.clips:
            return np.zeros((0, 2), dtype=np.float32), self.sample_rate

        # Sort clips by position
        self.clips.sort(key=lambda c: c.position)

        total = max(c.end_position for c in self.clips)
        out = np.zeros((total, 2), dtype=np.float32)

        for clip in self.clips:
            d = clip.audio_data
            if d is None or len(d) == 0:
                continue
            # Ensure stereo
            if d.ndim == 1:
                d = np.column_stack([d, d])
            elif d.shape[1] == 1:
                d = np.column_stack([d[:, 0], d[:, 0]])
            else:
                d = d[:, :2]

            s = clip.position
            e = min(s + len(d), total)
            n = e - s
            out[s:e] += d[:n].astype(np.float32)

        return out, self.sample_rate

    @property
    def total_duration_samples(self) -> int:
        return max((c.end_position for c in self.clips), default=0)

    @property
    def total_duration_seconds(self) -> float:
        return self.total_duration_samples / self.sample_rate if self.sample_rate > 0 else 0.0
