@echo off
chcp 65001 >nul
echo ========================================
echo    Glitch Maker v2.1 - Compilation .exe
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
