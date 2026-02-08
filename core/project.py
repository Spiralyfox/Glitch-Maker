"""
Project file management — .gspi format (ZIP with WAV clips + JSON metadata).
"""

import os
import json
import tempfile
import zipfile
import numpy as np
import soundfile as sf
from core.timeline import Timeline, AudioClip


def save_project(filepath: str, timeline: Timeline, sr: int, source_path: str = ""):
    """Save project as .gspi (ZIP with clips + metadata)."""
    with zipfile.ZipFile(filepath, 'w', zipfile.ZIP_DEFLATED) as zf:
        meta = {
            "version": "2.0",
            "sample_rate": sr,
            "source_path": source_path,
            "clips": [],
        }

        for i, clip in enumerate(timeline.clips):
            wav_name = f"clip_{i:03d}.wav"
            # Write clip audio to temp WAV then add to ZIP
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp.close()
            try:
                sf.write(tmp.name, clip.audio_data, clip.sample_rate, subtype="PCM_16")
                zf.write(tmp.name, wav_name)
            finally:
                os.unlink(tmp.name)

            meta["clips"].append({
                "name": clip.name,
                "file": wav_name,
                "position": clip.position,
                "color": clip.color,
            })

        zf.writestr("project.json", json.dumps(meta, indent=2))


def load_project(filepath: str) -> tuple[Timeline, int, str]:
    """Load a .gspi project. Returns (Timeline, sample_rate, source_path)."""
    tl = Timeline()

    with zipfile.ZipFile(filepath, 'r') as zf:
        meta = json.loads(zf.read("project.json"))
        sr = meta.get("sample_rate", 44100)
        source = meta.get("source_path", "")
        tl.sample_rate = sr

        colors = ["#533483", "#e94560", "#0f3460", "#16c79a", "#ff6b35", "#c74b50"]

        for i, cm in enumerate(meta["clips"]):
            wav_data = zf.read(cm["file"])
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp.write(wav_data)
            tmp.close()
            try:
                data, clip_sr = sf.read(tmp.name, dtype="float32", always_2d=True)
            finally:
                os.unlink(tmp.name)

            clip = AudioClip(
                name=cm.get("name", f"Clip {i+1}"),
                audio_data=data,
                sample_rate=clip_sr,
                position=cm.get("position", 0),
                color=cm.get("color", colors[i % len(colors)]),
            )
            tl.clips.append(clip)

    return tl, sr, source
