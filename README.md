# Glitch Maker v3.8

Application desktop d'edition et de glitching audio pour la production **digicore / hyperpop / glitchcore / dariacore**.

Interface sombre style DAW avec waveform interactive, timeline multi-clips, 28 effets audio, 25 presets, metronome et grille de temps.

![Python](https://img.shields.io/badge/Python-3.11+-blue) ![PyQt6](https://img.shields.io/badge/PyQt6-GUI-green) ![License](https://img.shields.io/badge/License-MIT-yellow)

## Installation

```bash
pip install -r requirements.txt
python main.py
```

Pour les formats MP3/M4A, installer FFmpeg :
```bash
winget install ffmpeg
```

## Compilation .exe

```bash
build.bat
```

Resultat dans `dist/Glitch.exe` (standalone, pas besoin de Python installe).

## Fonctionnalites

### 28 Effets audio (6 categories)

| Categorie | Effets |
|-----------|--------|
| **Basics** | Reverse, Volume, Filter (LP/HP/BP + sweep), Pan |
| **Pitch & Time** | Pitch Shift, Time Stretch, Tape Stop, Autotune (chromatique + gammes), Wave Ondulee |
| **Distortion** | Saturation (3 types), Distortion (fuzz/overdrive), Bitcrusher (bit depth + downsample) |
| **Modulation** | Chorus, Phaser, Tremolo, Ring Modulator |
| **Space & Texture** | Delay Feedback, Vinyl Crackle, OTT Compression, Voix Robotique, Hyper (one-knob hyperpop) |
| **Glitch** | Stutter, Granular, Slice Shuffle, Buffer Freeze, Datamosh, Vocal Chop, Tape Glitch |

Chaque effet a une fenetre de parametres avec preview audio en temps reel.

### 25 Presets

Presets classes par tags avec indicateur couleur :

- **Autotune** : Hard Autotune, Soft Autotune, Autotune + Reverb Wash
- **Hyperpop** : 100 gecs Mode, Hyperpop Maximum, Hyperpop Lite, Digital Angel, Nightcore Classic
- **Digicore / Dariacore** : Digicore Vocal Edit, Dariacore Chop, Dariacore Smash
- **Lo-fi / Tape** : Vinyl Nostalgia, Lo-fi Tape Mess, Tube Warmth
- **Ambient / Psychedelic** : Underwater, Dreamy Slowdown, Psycho Phaser, Wave Dream
- **Glitch / Experimental** : Electro Stutter, Sidechain Pulse, Fuzz Demon, Emocore Vocal
- **Vocal** : Robot Voice, Thick Chorus, Nightcore

Export / import de presets au format `.pspi`.

### Metronome & Grille de temps

- **Metronome** : clic de tempo synchronise a la lecture (BPM 20-300, volume, signature rythmique)
- **Grille** : overlay sur la waveform avec lignes de mesures, temps et subdivisions
- Choix de resolution : Bar, Beat, 1/2, 1/3, 1/4, 1/6, 1/8, 1/12, 1/16
- Controles BPM avec boutons +/- (auto-repeat) dans la toolbar

### Timeline avancee

- Clips audio avec drag & drop
- Clic droit : Couper, Dupliquer, Fade In/Out, Supprimer
- Effets appliques en 3 blocs (avant / effet / apres)
- Effets globaux non-destructifs sur toute la timeline

### Waveform interactive

- Zoom a la molette (centre sur curseur, jusqu'a x100)
- Selection par drag avec curseur bleu
- Playhead vert temps reel
- Grille de temps superposee

### Projet .gspi

Format de sauvegarde complet (ZIP avec clips WAV + metadata JSON).
Sauver / ouvrir via le menu Fichier ou drag & drop.

### Multi-langue

Interface disponible en francais et anglais (extensible).
Changement de langue instantane dans Options > Langue.

### Import de plugins

Possibilite d'importer des effets personnalises (fichiers `.py` avec classe `Plugin`).

## Raccourcis clavier

| Touche | Action |
|--------|--------|
| Espace | Play / Pause |
| Ctrl+Z | Annuler (30 niveaux) |
| Ctrl+Y | Retablir |
| Ctrl+O | Importer audio |
| Ctrl+S | Export WAV |
| Ctrl+Shift+S | Sauver projet |
| Ctrl+A | Tout selectionner |
| Escape | Deselectionner |
| Double-clic | Tout selectionner |
| Molette | Zoom waveform |

## Formats supportes

| Type | Formats |
|------|---------|
| Import | WAV, MP3, FLAC, OGG, M4A, AIFF |
| Export | WAV, MP3, FLAC |

## Stack technique

- **GUI** : PyQt6 (theme sombre custom)
- **Audio** : numpy, scipy, sounddevice, soundfile, librosa
- **Playback** : Stream low-latency (blocksize 256, ~6ms)
- **Build** : PyInstaller (standalone .exe)
