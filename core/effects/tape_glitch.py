"""
Tape Glitch — Random micro-glitches, wow/flutter, dropouts.
Lo-fi tape degradation for emo/digicore aesthetic.
"""
import numpy as np
from core.effects.utils import apply_micro_fade


def tape_glitch(audio_data, start, end, sr=44100,
                glitch_rate=0.4, dropout_chance=0.15,
                wow=0.3, flutter=0.4, noise=0.1):
    """
    Tape-style glitch effect.
    glitch_rate: density of micro-glitches (0-1)
    dropout_chance: probability of signal dropouts
    wow: slow pitch wobble (tape speed variation)
    flutter: fast pitch flutter
    noise: tape hiss amount
    """
    result = audio_data.copy()
    seg = result[start:end].copy().astype(np.float64)
    n = len(seg)
    if n < 64:
        return result
    is_stereo = seg.ndim == 2
    rng = np.random.RandomState(hash(n) % (2**31))

    t = np.arange(n, dtype=np.float64) / sr

    # ── 1. Wow (slow pitch wobble) ──
    if wow > 0.01:
        wow_freq = 0.5 + rng.random() * 1.5  # 0.5-2 Hz
        wow_signal = wow * 0.008 * np.sin(2 * np.pi * wow_freq * t +
                                           rng.random() * 2 * np.pi)
        speed = 1.0 + wow_signal
        read_idx = np.cumsum(speed)
        read_idx = read_idx / read_idx[-1] * (n - 1)
        i0 = np.clip(np.floor(read_idx).astype(int), 0, n - 1)
        i1 = np.clip(i0 + 1, 0, n - 1)
        frac = read_idx - i0
        if is_stereo:
            for ch in range(seg.shape[1]):
                seg[:, ch] = seg[i0, ch] * (1.0 - frac) + seg[i1, ch] * frac
        else:
            seg = seg[i0] * (1.0 - frac) + seg[i1] * frac

    # ── 2. Flutter (fast pitch variation) ──
    if flutter > 0.01:
        flutter_freq = 6.0 + rng.random() * 10.0  # 6-16 Hz
        flutter_sig = flutter * 0.004 * np.sin(2 * np.pi * flutter_freq * t)
        flutter_sig += flutter * 0.002 * np.sin(2 * np.pi * flutter_freq * 2.7 * t)
        speed = 1.0 + flutter_sig
        read_idx = np.cumsum(speed)
        read_idx = read_idx / read_idx[-1] * (n - 1)
        i0 = np.clip(np.floor(read_idx).astype(int), 0, n - 1)
        i1 = np.clip(i0 + 1, 0, n - 1)
        frac = read_idx - i0
        if is_stereo:
            for ch in range(seg.shape[1]):
                seg[:, ch] = seg[i0, ch] * (1.0 - frac) + seg[i1, ch] * frac
        else:
            seg = seg[i0] * (1.0 - frac) + seg[i1] * frac

    # ── 3. Micro-glitches (tiny repeated/frozen sections) ──
    if glitch_rate > 0.01:
        num_glitches = int(glitch_rate * n / sr * 15)  # ~15 glitches/sec at rate=1
        for _ in range(num_glitches):
            pos = rng.randint(0, max(1, n - 2048))
            glitch_len = rng.randint(64, min(2048, n - pos))
            glitch_type = rng.randint(0, 3)
            end_pos = min(pos + glitch_len, n)

            if glitch_type == 0:
                # Repeat a tiny slice
                repeat_src = rng.randint(0, max(1, n - glitch_len))
                src_end = min(repeat_src + glitch_len, n)
                copy_len = min(end_pos - pos, src_end - repeat_src)
                if copy_len > 0:
                    if is_stereo:
                        seg[pos:pos + copy_len] = seg[repeat_src:repeat_src + copy_len]
                    else:
                        seg[pos:pos + copy_len] = seg[repeat_src:repeat_src + copy_len]
            elif glitch_type == 1:
                # Reverse a tiny section
                if is_stereo:
                    seg[pos:end_pos] = seg[pos:end_pos][::-1]
                else:
                    seg[pos:end_pos] = seg[pos:end_pos][::-1]
            else:
                # Freeze (repeat first sample)
                if is_stereo:
                    seg[pos:end_pos] = seg[pos:pos + 1]
                else:
                    seg[pos:end_pos] = seg[pos]

    # ── 4. Signal dropouts ──
    if dropout_chance > 0.01:
        num_dropouts = max(1, int(dropout_chance * n / sr * 5))
        for _ in range(num_dropouts):
            if rng.random() < dropout_chance:
                pos = rng.randint(0, max(1, n - 4096))
                drop_len = rng.randint(128, min(4096, n - pos))
                fade = min(64, drop_len // 4)
                env = np.ones(drop_len)
                env[fade:-fade] = 0.0
                if fade > 0:
                    env[:fade] = np.linspace(1, 0, fade)
                    env[-fade:] = np.linspace(0, 1, fade)
                if is_stereo:
                    seg[pos:pos + drop_len] *= env[:, np.newaxis]
                else:
                    seg[pos:pos + drop_len] *= env

    # ── 5. Tape hiss ──
    if noise > 0.01:
        hiss = rng.normal(0, noise * 0.03, seg.shape)
        seg += hiss

    result[start:end] = apply_micro_fade(seg.astype(np.float32), 64)
    return np.clip(result, -1.0, 1.0)
