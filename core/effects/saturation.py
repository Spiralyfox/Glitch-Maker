"""
Effet Saturation — Hard Clip et Soft Clip.
Distortion agressive (100 gecs) ou chaude (Charli XCX).
"""

import numpy as np


def hard_clip(audio_data: np.ndarray, start: int, end: int,
              threshold: float = 0.5) -> np.ndarray:
    """
    Écrête le signal brutalement au-dessus du threshold.
    Plus le threshold est bas, plus c'est agressif.
    
    Args:
        threshold: Seuil d'écrêtage (0.1 = très distordu, 0.9 = léger)
    """
    result = audio_data.copy()
    threshold = max(0.05, min(1.0, threshold))
    result[start:end] = np.clip(result[start:end], -threshold, threshold)
    # Re-normaliser pour garder le volume
    result[start:end] = result[start:end] / threshold
    return np.clip(result, -1.0, 1.0)


def soft_clip(audio_data: np.ndarray, start: int, end: int,
              drive: float = 3.0) -> np.ndarray:
    """
    Saturation douce avec tanh — ajoute des harmoniques chaudes.
    
    Args:
        drive: Intensité de la saturation (1.0 = léger, 10.0 = très saturé)
    """
    result = audio_data.copy()
    drive = max(0.5, min(20.0, drive))
    result[start:end] = np.tanh(result[start:end] * drive)
    return result


def overdrive(audio_data: np.ndarray, start: int, end: int,
              gain: float = 5.0, tone: float = 0.5) -> np.ndarray:
    """
    Overdrive — combinaison de gain + soft clip + filtre.
    
    Args:
        gain: Gain d'entrée (1-20)
        tone: Brillance (0.0 = sombre, 1.0 = brillant)
    """
    result = audio_data.copy()
    segment = result[start:end].copy()
    
    # Gain
    segment = segment * gain
    
    # Soft clip asymétrique (plus musical)
    segment = np.where(
        segment >= 0,
        np.tanh(segment),
        np.tanh(segment * 0.8) * 1.2
    )
    
    # Tone (simple filtre passe-bas/haut via moyenne)
    if tone < 0.5 and segment.ndim >= 1:
        # Plus sombre : moyenne mobile
        kernel_size = int((1.0 - tone) * 8) + 1
        if segment.ndim == 1:
            segment = np.convolve(segment, np.ones(kernel_size)/kernel_size, mode='same')
        else:
            for ch in range(segment.shape[1]):
                segment[:, ch] = np.convolve(
                    segment[:, ch], np.ones(kernel_size)/kernel_size, mode='same'
                )
    
    result[start:end] = segment
    return np.clip(result, -1.0, 1.0)
