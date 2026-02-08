"""
Audio engine — multi-format loading, export.
MP3 export: lameenc (pure Python, no ffmpeg) > ffmpeg > pydub.
Other formats: soundfile > ffmpeg > pydub > librosa.
"""

import os
import sys
import subprocess
import tempfile
import shutil
import glob
import numpy as np
import soundfile as sf


# ═══════════════════════════════════════
# FFmpeg detection (cached)
# ═══════════════════════════════════════

_ffmpeg_cache = None
_ffmpeg_searched = False


def set_ffmpeg_path(path: str):
    """Manually set ffmpeg path (from settings or browse)."""
    global _ffmpeg_cache, _ffmpeg_searched
    if os.path.isfile(path):
        _ffmpeg_cache = path
        _ffmpeg_searched = True
        _sync_pydub_ffmpeg()
    else:
        raise FileNotFoundError(f"FFmpeg not found at: {path}")


def _load_ffmpeg_from_settings():
    """Try loading ffmpeg path from saved settings."""
    global _ffmpeg_cache, _ffmpeg_searched
    try:
        settings_path = os.path.join(os.path.expanduser("~"), ".glitchmaker_settings.json")
        if os.path.isfile(settings_path):
            import json as _json
            with open(settings_path, "r", encoding="utf-8") as f:
                s = _json.load(f)
            custom = s.get("ffmpeg_path", "")
            if custom and os.path.isfile(custom):
                _ffmpeg_cache = custom
                _ffmpeg_searched = True
                return True
    except Exception:
        pass
    return False


# Try settings first at import time
_load_ffmpeg_from_settings()


def _find_ffmpeg() -> str | None:
    global _ffmpeg_cache, _ffmpeg_searched
    if _ffmpeg_searched:
        return _ffmpeg_cache
    _ffmpeg_searched = True

    # 1. PATH
    path = shutil.which("ffmpeg")
    if path:
        _ffmpeg_cache = path
        return path

    # 2. Next to the app exe (PyInstaller or dev)
    app_dirs = []
    if getattr(sys, 'frozen', False):
        app_dirs.append(os.path.dirname(sys.executable))
    if sys.argv:
        app_dirs.append(os.path.dirname(os.path.abspath(sys.argv[0])))
    app_dirs.append(os.getcwd())
    for d in app_dirs:
        for name in ("ffmpeg.exe", "ffmpeg"):
            for sub in ["", os.path.join("ffmpeg", "bin")]:
                p = os.path.join(d, sub, name) if sub else os.path.join(d, name)
                if os.path.isfile(p):
                    _ffmpeg_cache = p
                    return p

    if os.name != 'nt':
        for p in ["/usr/bin/ffmpeg", "/usr/local/bin/ffmpeg",
                  os.path.expanduser("~/.local/bin/ffmpeg")]:
            if os.path.isfile(p):
                _ffmpeg_cache = p
                return p
        return None

    # ── Windows-specific search ──
    try:
        r = subprocess.run(["where", "ffmpeg"], capture_output=True, text=True, timeout=5,
                           creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
        if r.returncode == 0:
            for line in r.stdout.strip().splitlines():
                line = line.strip()
                if line and os.path.isfile(line):
                    _ffmpeg_cache = line
                    return line
    except Exception:
        pass

    candidates = []
    local = os.environ.get("LOCALAPPDATA", "")
    if local:
        candidates.append(os.path.join(local, "Microsoft", "WinGet", "Links", "ffmpeg.exe"))
        pkg_dir = os.path.join(local, "Microsoft", "WinGet", "Packages")
        if os.path.isdir(pkg_dir):
            candidates.extend(glob.glob(os.path.join(pkg_dir, "**", "ffmpeg.exe"), recursive=True))

    for drive in ["C:", "D:"]:
        for sub in [r"\ffmpeg\bin", r"\ffmpeg", r"\Program Files\ffmpeg\bin",
                    r"\Program Files (x86)\ffmpeg\bin", r"\Tools\ffmpeg\bin"]:
            candidates.append(f"{drive}{sub}\\ffmpeg.exe")

    user_home = os.path.expanduser("~")
    candidates.append(os.path.join(user_home, "scoop", "shims", "ffmpeg.exe"))
    candidates.append(os.path.join(user_home, "scoop", "apps", "ffmpeg", "current", "bin", "ffmpeg.exe"))
    candidates.append(r"C:\ProgramData\chocolatey\bin\ffmpeg.exe")

    for d in os.environ.get("PATH", "").split(os.pathsep):
        if d.strip():
            candidates.append(os.path.join(d.strip(), "ffmpeg.exe"))

    for folder in ["Downloads", "Desktop"]:
        fd = os.path.join(user_home, folder)
        if os.path.isdir(fd):
            candidates.extend(glob.glob(os.path.join(fd, "ffmpeg*", "**", "ffmpeg.exe"), recursive=True))

    seen = set()
    for p in candidates:
        if p in seen:
            continue
        seen.add(p)
        try:
            if os.path.isfile(p):
                _ffmpeg_cache = p
                return p
        except Exception:
            pass
    return None


def _sync_pydub_ffmpeg():
    ffmpeg = _find_ffmpeg()
    if ffmpeg:
        try:
            from pydub import AudioSegment
            AudioSegment.converter = ffmpeg
            d = os.path.dirname(ffmpeg)
            probe = os.path.join(d, "ffprobe.exe" if os.name == 'nt' else "ffprobe")
            if os.path.isfile(probe):
                AudioSegment.ffprobe = probe
        except Exception:
            pass


def ffmpeg_status() -> str:
    """Return human-readable FFmpeg status for diagnostics."""
    ffmpeg = _find_ffmpeg()
    if ffmpeg:
        try:
            r = subprocess.run([ffmpeg, "-version"], capture_output=True, text=True, timeout=5,
                               creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            ver = r.stdout.split('\n')[0] if r.stdout else "unknown version"
            return f"✅ FFmpeg found\n{ffmpeg}\n{ver}"
        except Exception:
            return f"⚠️ FFmpeg found but cannot run\n{ffmpeg}"
    return (
        "❌ FFmpeg NOT found\n\n"
        "MP3 export works without FFmpeg (built-in encoder).\n"
        "But M4A/AAC/OGG import requires FFmpeg.\n\n"
        "Install:\n"
        "  Windows:  winget install ffmpeg\n"
        "  Mac:      brew install ffmpeg\n"
        "  Linux:    sudo apt install ffmpeg\n\n"
        "Or use Options → Locate FFmpeg to browse\n"
        "for ffmpeg.exe on your system."
    )


# ═══════════════════════════════════════
# Loading
# ═══════════════════════════════════════

def load_audio(filepath: str) -> tuple[np.ndarray, int]:
    if not os.path.isfile(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    ext = os.path.splitext(filepath)[1].lower()
    errors = []

    # 1. soundfile (WAV, FLAC, OGG, AIFF)
    if ext in (".wav", ".flac", ".ogg", ".aiff"):
        try:
            data, sr = sf.read(filepath, dtype="float32", always_2d=True)
            return _ensure_stereo(data), sr
        except Exception as e:
            errors.append(f"soundfile: {e}")

    # 2. ffmpeg subprocess
    ffmpeg = _find_ffmpeg()
    if ffmpeg:
        tmp = None
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
            if tmp:
                try: os.unlink(tmp.name)
                except Exception: pass

    # 3. pydub
    try:
        _sync_pydub_ffmpeg()
        from pydub import AudioSegment
        seg = AudioSegment.from_file(filepath)
        sr = seg.frame_rate
        samples = np.array(seg.get_array_of_samples(), dtype=np.float32)
        samples /= float(2 ** (seg.sample_width * 8 - 1))
        samples = samples.reshape(-1, seg.channels)
        return _ensure_stereo(samples), sr
    except Exception as e:
        errors.append(f"pydub: {e}")

    # 4. librosa
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

    # Build helpful error
    fname = os.path.basename(filepath)
    needs_ffmpeg = ext in (".mp3", ".m4a", ".aac", ".wma", ".opus")
    if needs_ffmpeg:
        raise RuntimeError(
            f"Cannot load '{fname}'.\n\n"
            f"{ext.upper()} files require FFmpeg to decode.\n\n"
            f"Install FFmpeg:\n"
            f"  Windows:  winget install ffmpeg\n"
            f"  Mac:      brew install ffmpeg\n"
            f"  Linux:    sudo apt install ffmpeg\n\n"
            f"Or place ffmpeg.exe next to GlitchMaker.exe,\n"
            f"then RESTART the app.\n\n"
            f"Tip: WAV and FLAC files load without FFmpeg."
        )
    raise RuntimeError(
        f"Cannot load '{fname}'.\n\n"
        + "\n".join(errors)
    )


# ═══════════════════════════════════════
# Export
# ═══════════════════════════════════════

def export_wav(data: np.ndarray, sr: int, filepath: str):
    sf.write(filepath, data, sr, subtype="PCM_16")


def _export_mp3_lameenc(data: np.ndarray, sr: int, filepath: str):
    """Pure Python MP3 export using lameenc — no ffmpeg needed."""
    import lameenc

    # Convert float32 stereo to interleaved int16
    clipped = np.clip(data, -1.0, 1.0)
    pcm_int16 = (clipped * 32767).astype(np.int16)
    pcm_bytes = pcm_int16.tobytes()

    channels = data.shape[1] if data.ndim > 1 else 1

    encoder = lameenc.Encoder()
    encoder.set_bit_rate(192)
    encoder.set_in_sample_rate(sr)
    encoder.set_channels(channels)
    encoder.set_quality(2)  # 2=high quality, 7=fast

    mp3_data = encoder.encode(pcm_bytes)
    mp3_data += encoder.flush()

    with open(filepath, "wb") as f:
        f.write(mp3_data)


def export_audio(data: np.ndarray, sr: int, filepath: str, fmt: str = "wav"):
    if fmt == "wav":
        export_wav(data, sr, filepath)
        return

    # FLAC: soundfile native — no ffmpeg needed
    if fmt == "flac":
        try:
            sf.write(filepath, data, sr, format="FLAC")
            return
        except Exception:
            pass

    # MP3: try lameenc first (pure Python, always works)
    if fmt == "mp3":
        try:
            _export_mp3_lameenc(data, sr, filepath)
            if os.path.isfile(filepath) and os.path.getsize(filepath) > 0:
                return
        except ImportError:
            pass  # lameenc not installed, fall through to ffmpeg
        except Exception as e:
            pass  # encoding failed, try ffmpeg

    if fmt not in ("mp3", "ogg"):
        raise ValueError(f"Unsupported format: {fmt}")

    # ffmpeg path
    ffmpeg = _find_ffmpeg()
    if ffmpeg:
        tmp = None
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp.close()
            export_wav(data, sr, tmp.name)
            codec = {"mp3": "libmp3lame", "ogg": "libvorbis"}[fmt]
            cmd = [ffmpeg, "-y", "-i", tmp.name, "-acodec", codec]
            if fmt == "mp3":
                cmd.extend(["-b:a", "192k"])
            cmd.append(filepath)
            result = subprocess.run(
                cmd, capture_output=True, timeout=60,
                creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
            if result.returncode == 0 and os.path.isfile(filepath):
                os.unlink(tmp.name)
                return
        except Exception:
            pass
        finally:
            if tmp:
                try: os.unlink(tmp.name)
                except Exception: pass

    # pydub fallback
    tmp = None
    try:
        _sync_pydub_ffmpeg()
        from pydub import AudioSegment
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        export_wav(data, sr, tmp.name)
        AudioSegment.from_wav(tmp.name).export(filepath, format=fmt)
        os.unlink(tmp.name)
        if os.path.isfile(filepath):
            return
    except Exception:
        if tmp:
            try: os.unlink(tmp.name)
            except Exception: pass

    raise RuntimeError(
        f"Cannot export to {fmt.upper()}.\n\n"
        f"FFmpeg is required for {fmt.upper()} export.\n\n"
        f"Install FFmpeg:\n"
        f"  Windows:  winget install ffmpeg\n"
        f"  Mac:      brew install ffmpeg\n"
        f"  Linux:    sudo apt install ffmpeg\n\n"
        f"Or place ffmpeg.exe next to GlitchMaker.exe,\n"
        f"then restart the app."
    )


# ═══════════════════════════════════════
# Utilities
# ═══════════════════════════════════════

def _ensure_stereo(data: np.ndarray) -> np.ndarray:
    if data.ndim == 1:
        return np.column_stack([data, data]).astype(np.float32)
    if data.shape[1] == 1:
        return np.column_stack([data[:, 0], data[:, 0]]).astype(np.float32)
    out = data[:, :2]
    if out.dtype != np.float32:
        out = out.astype(np.float32)
    return out


def ensure_stereo(data: np.ndarray) -> np.ndarray:
    return _ensure_stereo(data)


def audio_to_mono(data: np.ndarray) -> np.ndarray:
    if data.ndim == 1:
        return data.astype(np.float32)
    return np.mean(data, axis=1).astype(np.float32)


def get_duration(data: np.ndarray, sr: int) -> float:
    return len(data) / sr


def format_time(seconds: float) -> str:
    m = int(seconds // 60)
    s = seconds % 60
    return f"{m:02d}:{s:05.2f}"
