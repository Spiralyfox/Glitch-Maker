# Glitch v1.0

Application desktop de glitching audio pour la production digicore / hyperpop / glitchcore.

## Installation

```bash
pip install -r requirements.txt
python main.py
```

Pour MP3/M4A, installer FFmpeg : `winget install ffmpeg`

## Compilation .exe

```bash
build.bat
```

Resultat dans `dist/Glitch.exe`.

## Fonctionnalites

### 16 Effets audio

**Core :** Stutter, Bitcrusher, Saturation (3 types), Reverse, Pitch Shift, Time Stretch

**Avances :** Granular, Tape Stop, Buffer Freeze, Delay Feedback, Ring Modulator, Filtre Resonant, OTT Compression, Vinyl Crackle, Datamosh, Shuffle

### 5 Presets

Light Glitch, Digicore Vocal, 100 gecs Mode, Tape Wreck, Dariacore Chop

### Timeline avancee

- Clic droit sur un clip : Couper, Dupliquer, Fade In/Out, Supprimer
- Waveform avec zoom molette, selection par drag
- Effets appliques en 3 blocs (avant / effet / apres)

### Projet .gspi

Format de sauvegarde propre (ZIP avec clips WAV + metadata JSON).
Ouvrir / sauver via Fichier ou drag & drop.

### Raccourcis

| Touche | Action |
|--------|--------|
| Space | Play / Pause |
| Ctrl+Z | Annuler |
| Ctrl+Y | Retablir |
| Ctrl+O | Importer audio |
| Ctrl+S | Export WAV |
| Ctrl+Shift+S | Sauver projet |
| Ctrl+Shift+O | Ouvrir projet |
| Ctrl+A | Tout selectionner |
| Escape | Deselectionner |
| Double-clic | Tout selectionner |

### Formats supportes

Import : WAV, MP3, FLAC, OGG, M4A, AIFF
Export : WAV, MP3, FLAC

## Stack technique

Python 3.11+ / PyQt6 / numpy / scipy / sounddevice / soundfile / librosa
