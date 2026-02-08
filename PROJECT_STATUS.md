# Glitch Maker — Statut du projet

## v3.8 — Release actuelle

### Phase 1 : Fondations [COMPLETE]
- GUI PyQt6 theme sombre digicore
- Waveform interactive (zoom molette x100, selection, curseur bleu, playhead vert)
- Playback temps reel low-latency (sounddevice, blocksize 256, ~6ms)
- Enregistrement micro
- Timeline avec clips drag & drop
- Import multi-format (WAV, MP3, FLAC, OGG, M4A, AIFF)
- Export WAV / MP3 / FLAC (via FFmpeg)
- Drag & drop fichiers
- Projet .gspi (ZIP avec clips WAV + metadata JSON)

### Phase 2 : Effets Core (10 effets) [COMPLETE]
- Reverse
- Volume / Pan
- Filter resonant (LP/HP/BP + Sweep)
- Pitch Shift (corrige + simple)
- Time Stretch
- Tape Stop
- Saturation (Hard Clip, Soft Clip, Overdrive)
- Distortion (Fuzz, Overdrive, Crunch)
- Bitcrusher (bit depth + downsample)

### Phase 3 : Effets avances (11 effets) [COMPLETE]
- Autotune (chromatique + 8 gammes, vitesse variable)
- Wave Ondulee (pitch LFO)
- Chorus / Phaser / Tremolo
- Ring Modulator
- Delay Feedback
- Vinyl Crackle
- OTT Compression multiband

### Phase 4 : Effets Glitch & Texture (7 effets) [COMPLETE]
- Stutter / Repeat (3 modes)
- Granular Glitch
- Slice Shuffle
- Buffer Freeze
- Datamosh Audio
- Vocal Chop
- Tape Glitch

### Phase 5 : Effets Speciaux (2 effets) [COMPLETE]
- Voix Robotique (granulaire + ring mod + monotone)
- Hyper (one-knob hyperpop: saturation + shimmer + brightness)

### Phase 6 : Presets & UX [COMPLETE]
- 25 presets organises par tags (Autotune, Hyperpop, Digicore, Lo-fi, Ambient, etc.)
- Affichage compact avec pastilles couleur par tag
- Tooltips avec description au survol
- Sections repliables avec compteur
- Export / import presets .pspi
- Gestionnaire de presets et tags

### Phase 7 : Timeline avancee [COMPLETE]
- Clic droit : Split, Duplicate, Delete, Fade In/Out
- Undo / Redo (Ctrl+Z / Ctrl+Y, 30 niveaux)
- Split en 3 clips (avant / effet / apres)
- Effets globaux non-destructifs
- Confirmation a la fermeture si non sauvegarde

### Phase 8 : Metronome & Grille [COMPLETE]
- Metronome avec clic synchronise a la lecture (accent sur temps 1)
- BPM configurable 20-300 avec boutons +/- (auto-repeat)
- Signature rythmique configurable (1-12 beats/mesure)
- Volume metronome independant
- Grille de temps sur la waveform (style FL Studio)
- Resolutions : Bar, Beat, 1/2, 1/3, 1/4, 1/6, 1/8, 1/12, 1/16
- Lignes de mesures (lumineuses), temps (moyennes), subdivisions (legeres)
- Numerotation des mesures

### Phase 9 : Polish & Qualite [COMPLETE]
- Multi-langue (FR/EN) avec changement instantane
- Import de plugins personnalises (.py)
- Preview audio en temps reel dans les dialogues d'effets
- Catalogue complet des effets avec descriptions
- Menus propres avec raccourcis clavier
- Build script .exe (PyInstaller)
- Playback low-latency (blocksize 256, latency='low')

## Statistiques

| Element | Nombre |
|---------|--------|
| Effets audio | 28 |
| Categories d'effets | 6 |
| Presets | 25 |
| Tags de presets | 19 |
| Langues | 2 (FR, EN) |
| Formats import | 6 |
| Formats export | 3 |
| Niveaux undo/redo | 30 |
