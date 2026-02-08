"""
Example user plugin for Glitch Maker.
Copy this template to create your own effects.

Required:
  METADATA  — dict with id, name, icon, color, section
  PARAMS    — list of parameter definitions (can be empty [])
  process() — function that processes audio

Parameter types:
  "int"    → slider + spinbox (min, max, default, suffix)
  "float"  → slider + spinbox (min, max, default, step, decimals, suffix)
  "choice" → dropdown (options list, default)
  "bool"   → checkbox (default)
"""
import numpy as np

METADATA = {
    "id": "example_wobble",
    "name": "Wobble",
    "icon": "W",
    "color": "#e07c24",
    "section": "Custom",
}

PARAMS = [
    {"key": "rate", "label": "Rate (Hz)", "type": "float",
     "min": 0.5, "max": 20.0, "default": 5.0, "step": 0.5, "decimals": 1},
    {"key": "depth", "label": "Depth", "type": "float",
     "min": 0.0, "max": 1.0, "default": 0.5},
    {"key": "shape", "label": "Shape", "type": "choice",
     "options": ["sine", "triangle", "square"], "default": "sine"},
]


def process(audio_data, start, end, sr=44100, **kw):
    """Apply a wobble (amplitude modulation) effect."""
    rate = kw.get("rate", 5.0)
    depth = kw.get("depth", 0.5)
    shape = kw.get("shape", "sine")

    segment = audio_data[start:end].copy()
    n = len(segment)
    t = np.arange(n) / sr

    # Generate modulation signal
    if shape == "sine":
        mod = np.sin(2 * np.pi * rate * t)
    elif shape == "triangle":
        mod = 2 * np.abs(2 * (rate * t % 1) - 1) - 1
    else:  # square
        mod = np.sign(np.sin(2 * np.pi * rate * t))

    # Apply amplitude modulation
    envelope = 1.0 - depth * 0.5 * (1.0 + mod)

    if segment.ndim == 2:
        envelope = envelope[:, np.newaxis]

    audio_data[start:end] = segment * envelope
    return audio_data
