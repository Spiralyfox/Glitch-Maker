@echo off
chcp 65001 >nul
echo ========================================
echo    Glitch Maker v2.2 - Compilation .exe
echo ========================================
echo.

REM S'assurer qu'on est dans le bon dossier (celui du .bat)
cd /d "%~dp0"

echo [1/3] Installation des dependances...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERREUR installation
    pause
    exit /b 1
)

echo.
echo [2/3] Compilation avec PyInstaller...
pyinstaller ^
    --onefile ^
    --windowed ^
    --name "GlitchMaker" ^
    --add-data "assets;assets" ^
    --add-data "lang;lang" ^
    --hidden-import sounddevice ^
    --hidden-import soundfile ^
    --hidden-import numpy ^
    --hidden-import scipy ^
    --hidden-import scipy.signal ^
    --hidden-import pydub ^
    --hidden-import librosa ^
    --hidden-import librosa.util ^
    --hidden-import lameenc ^
    --hidden-import plugins ^
    --hidden-import plugins.loader ^
    --hidden-import plugins.preview_player ^
    --hidden-import core.effects.reverse ^
    --hidden-import core.effects.volume ^
    --hidden-import core.effects.filter ^
    --hidden-import core.effects.pan ^
    --hidden-import core.effects.pitch_shift ^
    --hidden-import core.effects.time_stretch ^
    --hidden-import core.effects.tape_stop ^
    --hidden-import core.effects.saturation ^
    --hidden-import core.effects.distortion ^
    --hidden-import core.effects.bitcrusher ^
    --hidden-import core.effects.chorus ^
    --hidden-import core.effects.phaser ^
    --hidden-import core.effects.tremolo ^
    --hidden-import core.effects.ring_mod ^
    --hidden-import core.effects.delay ^
    --hidden-import core.effects.vinyl ^
    --hidden-import core.effects.ott ^
    --hidden-import core.effects.stutter ^
    --hidden-import core.effects.granular ^
    --hidden-import core.effects.shuffle ^
    --hidden-import core.effects.buffer_freeze ^
    --hidden-import core.effects.datamosh ^
    main.py

if %errorlevel% neq 0 (
    echo ERREUR compilation
    pause
    exit /b 1
)

echo.
echo [3/3] Nettoyage...
rmdir /S /Q build >nul 2>&1
del /Q GlitchMaker.spec >nul 2>&1

echo.
echo ========================================
echo    OK : dist\GlitchMaker.exe
echo ========================================
echo.
echo Pour lancer : dist\GlitchMaker.exe
pause
