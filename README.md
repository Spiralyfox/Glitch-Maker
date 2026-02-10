# Glitch Maker 🎵

## 🇫🇷 Français

**Glitch Maker** est une station de travail d'effets audio créatifs conçue pour le sound design, le glitch art sonore et l'expérimentation musicale. Chargez n'importe quel fichier audio (MP3, WAV, FLAC, OGG…) et appliquez des effets destructifs, modulaires ou texturants en temps réel sur tout ou partie du signal.

### Ce que fait Glitch Maker

Glitch Maker permet de transformer radicalement un fichier audio en lui appliquant des chaînes d'effets non-destructifs. Chaque effet s'ajoute comme une couche que vous pouvez activer, désactiver ou supprimer à tout moment via l'historique. Le logiciel découpe visuellement votre audio en clips sur une timeline, et vous pouvez sélectionner précisément la zone à traiter grâce à la sélection rouge sur la waveform.

### Fonctionnalités principales

**Interface complète** — Waveform interactive avec zoom indépendant, timeline multi-clips, minimap de navigation, analyseur de spectre en temps réel, métronome synchronisé avec grille de tempo, et transport complet (Play/Pause/Stop avec boucle automatique).

**27 effets audio** organisés en 6 catégories :
- **Basics** — Reverse, Volume, Filter, Pan/Stereo : les outils fondamentaux pour manipuler le signal.
- **Pitch & Time** — Pitch Shift, Time Stretch, Tape Stop, Autotune, Pitch Drift : modifiez la hauteur et la vitesse du son.
- **Distortion** — Saturation, Distortion, Bitcrusher : écrasez, saturez et dégradez volontairement le signal.
- **Modulation** — Chorus, Phaser, Tremolo, Ring Mod : créez du mouvement et de la profondeur.
- **Space & Texture** — Delay, Vinyl, OTT, Robotic Voice, Hyper : ajoutez de l'espace, de la texture et des ambiances.
- **Glitch** — Stutter, Granular, Shuffle, Buffer Freeze, Datamosh, Vocal Chop, Tape Glitch : les effets destructifs et expérimentaux.

**Système non-destructif** — Chaque effet est enregistré dans un historique. Vous pouvez les activer/désactiver individuellement, les supprimer, et utiliser Ctrl+Z / Ctrl+Y pour annuler/refaire.

**Sélection intelligente** — Pendant la lecture, démarrer une sélection met automatiquement en pause. En relâchant, la lecture reprend dans la zone sélectionnée. Si vous changez de sélection pendant une pause, la lecture reprend dans la nouvelle zone.

**Timeline multi-clips** — Assemblez plusieurs fichiers audio dans un même projet grâce au bouton ＋ de la barre de transport. Supprimez un clip via clic droit ou touche Suppr : les clips restants se repositionnent automatiquement pour combler les vides.

**Édition** — Coupez des portions d'audio (remplacement par du silence ou suppression avec recollage), placez des marqueurs, et naviguez entre eux.

**Presets & Plugins** — Créez des presets avec chaînes d'effets configurables (bouton Settings par effet). Testez-les en direct avant de sauvegarder (Play original / Play with preset). Gérez vos presets via une interface à onglets : "My Presets" (triés par tags, modifiables, supprimables) et "Built-in" (lecture seule). Les noms de presets et les effets dans une chaîne sont uniques (pas de doublons). Importez/exportez au format .pspi. Importez des plugins d'effets personnalisés (.py) — consultez la page d'exemple de code intégrée dans l'aide pour créer les vôtres.

**Multi-langue** — Interface disponible en français et en anglais.

**Personnalisation** — Thème sombre/clair, réglages audio (entrée/sortie) avec actualisation des périphériques, métronome configurable (BPM, volume).

### Installation & Lancement

**Option 1 — Lancer directement avec Python :**

```bash
pip install -r requirements.txt
python main.py
```

**Option 2 — Compiler en .exe (Windows) :**

Double-cliquez sur `build.bat` — le script installe automatiquement les dépendances, compile le projet avec PyInstaller, et génère `dist\GlitchMaker.exe`. Lancez ensuite le .exe depuis le dossier `dist\`.

**Données utilisateur :** Toutes vos données (paramètres, presets, tags, logs) sont stockées dans un dossier `data\` créé automatiquement à côté du .exe ou du main.py. Pour un reset complet, supprimez ce dossier.

FFmpeg est téléchargé automatiquement au premier lancement si nécessaire (pour le support MP3/FLAC/OGG).

### Raccourcis clavier

| Raccourci | Action |
|---|---|
| Espace | Lecture / Pause |
| Escape | Désélectionner |
| Ctrl+Z | Annuler |
| Ctrl+Y | Refaire |
| M | Ajouter un marqueur |
| Ctrl+← / Ctrl+→ | Marqueur précédent / suivant |
| Suppr | Supprimer le clip sélectionné |
| Molette (waveform) | Zoom waveform |
| Molette (timeline) | Zoom timeline |

---

## 🇬🇧 English

**Glitch Maker** is a creative audio effects workstation designed for sound design, audio glitch art and musical experimentation. Load any audio file (MP3, WAV, FLAC, OGG…) and apply destructive, modular or texturing effects in real time on all or part of the signal.

### What Glitch Maker does

Glitch Maker lets you radically transform an audio file by applying non-destructive effect chains. Each effect is added as a layer that you can enable, disable or delete at any time via the history panel. The software visually slices your audio into clips on a timeline, and you can precisely select the area to process using the red selection on the waveform.

### Key features

**Complete interface** — Interactive waveform with independent zoom, multi-clip timeline, navigation minimap, real-time spectrum analyzer, metronome synchronized with beat grid, and full transport (Play/Pause/Stop with automatic looping).

**27 audio effects** organized in 6 categories:
- **Basics** — Reverse, Volume, Filter, Pan/Stereo: fundamental tools to manipulate the signal.
- **Pitch & Time** — Pitch Shift, Time Stretch, Tape Stop, Autotune, Pitch Drift: modify pitch and speed.
- **Distortion** — Saturation, Distortion, Bitcrusher: crush, saturate and deliberately degrade the signal.
- **Modulation** — Chorus, Phaser, Tremolo, Ring Mod: create movement and depth.
- **Space & Texture** — Delay, Vinyl, OTT, Robotic Voice, Hyper: add space, texture and atmospheres.
- **Glitch** — Stutter, Granular, Shuffle, Buffer Freeze, Datamosh, Vocal Chop, Tape Glitch: destructive and experimental effects.

**Non-destructive system** — Every effect is recorded in a history. You can enable/disable them individually, delete them, and use Ctrl+Z / Ctrl+Y to undo/redo.

**Smart selection** — While audio is playing, starting a selection automatically pauses playback. On release, playback resumes inside the selected zone. If you change the selection while paused, playback resumes in the new zone.

**Multi-clip timeline** — Combine multiple audio files into one project using the ＋ button in the transport bar. Delete a clip via right-click or the Delete key: remaining clips automatically reposition to close gaps.

**Editing** — Cut portions of audio (replace with silence or splice), place markers, and navigate between them.

**Presets & Plugins** — Create presets with configurable effect chains (Settings button per effect). Test them live before saving (Play original / Play with preset). Manage presets via a tabbed interface: "My Presets" (sorted by tags, editable, deletable) and "Built-in" (read-only). Preset names and effects within a chain are unique (no duplicates). Import/export as .pspi files. Import custom effect plugins (.py) — check the built-in code example page in Help to create your own.

**Multi-language** — Interface available in French and English.

**Customization** — Dark/light theme, audio settings (input/output) with device refresh, configurable metronome (BPM, volume).

### Installation & Launch

**Option 1 — Run directly with Python:**

```bash
pip install -r requirements.txt
python main.py
```

**Option 2 — Compile to .exe (Windows):**

Double-click `build.bat` — the script automatically installs dependencies, compiles the project with PyInstaller, and generates `dist\GlitchMaker.exe`. Then launch the .exe from the `dist\` folder.

**User data:** All your data (settings, presets, tags, logs) is stored in a `data\` folder automatically created next to the .exe or main.py. For a full reset, just delete this folder.

FFmpeg is automatically downloaded on first launch if needed (for MP3/FLAC/OGG support).

### Keyboard shortcuts

| Shortcut | Action |
|---|---|
| Space | Play / Pause |
| Escape | Deselect |
| Ctrl+Z | Undo |
| Ctrl+Y | Redo |
| M | Add marker |
| Ctrl+← / Ctrl+→ | Previous / next marker |
| Delete | Delete selected clip |
| Scroll wheel (waveform) | Waveform zoom |
| Scroll wheel (timeline) | Timeline zoom |

---

## Crédits / Credits

**Auteur / Author** : Mattéo Dauriac (Spiralyfox)

**Projet / Project** : [github.com/Spiralyfox/GlitchMaker](https://github.com/Spiralyfox/GlitchMaker)

**GitHub** : [github.com/Spiralyfox](https://github.com/Spiralyfox)

Built with Python, PyQt6, NumPy, SciPy, sounddevice, soundfile.
