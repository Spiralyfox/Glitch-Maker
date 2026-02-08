"""
Audio engine — multi-format loading, export.
Fallback chain: soundfile > ffmpeg subprocess > pydub > librosa.
"""

import os
import subprocess
import tempfile
import shutil
import glob
import numpy as np
import soundfile as sf


def load_audio(filepath: str) -> tuple[np.ndarray, int]:
    """Load an audio file. Tries 4 methods in cascade."""
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    ext = os.path.splitext(filepath)[1].lower()
    errors = []

    # Method 1: soundfile direct (WAV, FLAC, OGG, AIFF)
    if ext in (".wav", ".flac", ".ogg", ".aiff"):
        try:
            data, sr = sf.read(filepath, dtype="float32", always_2d=True)
            return _ensure_stereo(data), sr
        except Exception as e:
            errors.append(f"soundfile: {e}")

    # Method 2: ffmpeg subprocess → WAV temp → soundfile
    ffmpeg = _find_ffmpeg()
    if ffmpeg:
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp.close()
            cmd = [ffmpeg, "-y", "-i", filepath, "-acodec", "pcm_s16le",
                   "-ar", "44100", "-ac", "2", tmp.name]
            subprocess.run(cmd, capture_output=True, check=True, timeout=30,
                           creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            data, sr = sf.read(tmp.name, dtype="float32", always_2d=True)
            os.unlink(tmp.name)
            return _ensure_stereo(data), sr
        except Exception as e:
            errors.append(f"ffmpeg: {e}")
            try:
                os.unlink(tmp.name)
            except Exception:
                pass
    else:
        errors.append("ffmpeg: not found in PATH")

    # Method 3: pydub (uses ffmpeg internally too)
    try:
        from pydub import AudioSegment
        seg = AudioSegment.from_file(filepath)
        sr = seg.frame_rate
        samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
        samples /= float(2 ** (seg.sample_width * 8 - 1))
        samples = samples.reshape(-1, seg.channels)
        return _ensure_stereo(samples), sr
    except Exception as e:
        errors.append(f"pydub: {e}")

    # Method 4: librosa (audioread backend)
    try:
        import librosa
        y, sr = librosa.load(filepath, sr=None, mono=False)
        if y.ndim == 1:
            data = np.column_stack([y, y])
        else:
            data = y.T
        return _ensure_stereo(data.astype(np.float32)), sr
    except Exception as e:
        errors.append(f"librosa: {e}")

    raise RuntimeError(
        f"Cannot load '{os.path.basename(filepath)}'.\n\n"
        f"MP3/M4A/AAC files require FFmpeg.\n"
        f"Install it:\n"
        f"  Windows:  winget install ffmpeg\n"
        f"  Mac:      brew install ffmpeg\n"
        f"  Linux:    sudo apt install ffmpeg\n\n"
        f"IMPORTANT: After installing, close and reopen Glitch Maker\n"
        f"(the app needs a fresh start to detect FFmpeg).\n\n"
        f"Details:\n" + "\n".join(errors)
    )


def _find_ffmpeg() -> str | None:
    """Find ffmpeg in PATH or common locations. Very thorough on Windows."""
    # 1. Check PATH
    path = shutil.which("ffmpeg")
    if path:
        return path

    # 2. On Windows, try 'where' command (catches PATH entries not seen by shutil.which)
    if os.name == 'nt':
        try:
            r = subprocess.run(["where", "ffmpeg"], capture_output=True, text=True, timeout=5,
                               creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            if r.returncode == 0:
                for line in r.stdout.strip().splitlines():
                    line = line.strip()
                    if line and os.path.isfile(line):
                        return line
        except Exception:
            pass

    candidates = []

    # 3. WinGet locations (most common on Windows 10/11)
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        # WinGet Links (symlinks, should be in PATH but sometimes isn't)
        candidates.append(os.path.join(local, "Microsoft", "WinGet", "Links", "ffmpeg.exe"))

        # WinGet Packages — deep glob for any ffmpeg.exe
        pkg_dir = os.path.join(local, "Microsoft", "WinGet", "Packages")
        if os.path.isdir(pkg_dir):
            # Pattern: Gyan.FFmpeg_*/ffmpeg-*/bin/ffmpeg.exe
            candidates.extend(glob.glob(os.path.join(pkg_dir, "Gyan.FFmpeg*", "**", "ffmpeg.exe"), recursive=True))
            # Also broader pattern
            candidates.extend(glob.glob(os.path.join(pkg_dir, "*ffmpeg*", "**", "ffmpeg.exe"), recursive=True))
            candidates.extend(glob.glob(os.path.join(pkg_dir, "*FFmpeg*", "**", "ffmpeg.exe"), recursive=True))

    # 4. Common manual install locations
    candidates.extend([
        r"C:\ffmpeg\bin\ffmpeg.exe",
        r"C:\ffmpeg\ffmpeg.exe",
        r"C:\Program Files\ffmpeg\bin\ffmpeg.exe",
        r"C:\Program Files (x86)\ffmpeg\bin\ffmpeg.exe",
    ])

    # 5. Scoop
    user_home = os.path.expanduser("~")
    candidates.append(os.path.join(user_home, "scoop", "shims", "ffmpeg.exe"))
    candidates.append(os.path.join(user_home, "scoop", "apps", "ffmpeg", "current", "bin", "ffmpeg.exe"))

    # 6. Chocolatey
    candidates.append(r"C:\ProgramData\chocolatey\bin\ffmpeg.exe")

    # 7. Check PATH env variable manually (sometimes shutil.which misses entries)
    for d in os.environ.get("PATH", "").split(os.pathsep):
        fp = os.path.join(d.strip(), "ffmpeg.exe" if os.name == 'nt' else "ffmpeg")
        if fp not in candidates:
            candidates.append(fp)

    seen = set()
    for p in candidates:
        if p in seen:
            continue
        seen.add(p)
        try:
            if os.path.isfile(p):
                return p
        except Exception:
            pass
    return None


def _ensure_stereo(data: np.ndarray) -> np.ndarray:
    """Force stereo float32."""
    if data.ndim == 1:
        return np.column_stack([data, data]).astype(np.float32)
    if data.shape[1] == 1:
        return np.column_stack([data[:, 0], data[:, 0]]).astype(np.float32)
    return data[:, :2].astype(np.float32)


def ensure_stereo(data: np.ndarray) -> np.ndarray:
    return _ensure_stereo(data)


def audio_to_mono(data: np.ndarray) -> np.ndarray:
    if data.ndim == 1:
        return data.astype(np.float32)
    return np.mean(data, axis=1).astype(np.float32)


def export_wav(data: np.ndarray, sr: int, filepath: str):
    sf.write(filepath, data, sr, subtype="PCM_16")


def export_audio(data: np.ndarray, sr: int, filepath: str, fmt: str = "wav"):
    """Export in the requested format."""
    if fmt == "wav":
        export_wav(data, sr, filepath)
    elif fmt in ("mp3", "flac", "ogg"):
        ffmpeg = _find_ffmpeg()
        if ffmpeg:
            try:
                tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
                tmp.close()
                export_wav(data, sr, tmp.name)
                codec = {"mp3": "libmp3lame", "flac": "flac", "ogg": "libvorbis"}[fmt]
                cmd = [ffmpeg, "-y", "-i", tmp.name, "-acodec", codec, filepath]
                subprocess.run(cmd, capture_output=True, check=True, timeout=60,
                               creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                os.unlink(tmp.name)
                return
            except Exception:
                try:
                    os.unlink(tmp.name)
                except Exception:
                    pass
        # Fallback pydub
        from pydub import AudioSegment
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        export_wav(data, sr, tmp.name)
        AudioSegment.from_wav(tmp.name).export(filepath, format=fmt)
        os.unlink(tmp.name)
    else:
        raise ValueError(f"Unsupported format: {fmt}")


def get_duration(data: np.ndarray, sr: int) -> float:
    return len(data) / sr


def format_time(seconds: float) -> str:
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m:02d}:{s:05.2f}"
