@echo off
echo Starting DoubleSub.io locally...
echo.

REM Check Python
python --version
if %errorlevel% neq 0 (
    echo Python n'est pas installe ou pas dans le PATH
    pause
    exit /b 1
)

REM Create or recreate venv if needed
if not exist "venv\Scripts\python.exe" (
    echo Creation de l'environnement virtuel...
    if exist "venv" rmdir /s /q venv
    python -m venv venv
)

echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat

echo Installation des dependances...
venv\Scripts\pip install -r requirements.txt --quiet

REM Check if FFmpeg is in local folder
set "LOCAL_FFMPEG=%~dp0ffmpeg\bin\ffmpeg.exe"
set "LOCAL_FFPROBE=%~dp0ffmpeg\bin\ffprobe.exe"

if exist "%LOCAL_FFMPEG%" (
    echo FFmpeg local trouve: %LOCAL_FFMPEG%
    set "FFMPEG_PATH=%LOCAL_FFMPEG%"
    set "FFPROBE_PATH=%LOCAL_FFPROBE%"
    goto :start_server
)

REM Check FFmpeg in system PATH
ffmpeg -version >nul 2>&1
if %errorlevel% equ 0 (
    echo FFmpeg systeme trouve dans le PATH
    goto :start_server
)

REM FFmpeg not found - offer to download
echo.
echo ========================================
echo  FFmpeg n'est pas installe
echo ========================================
echo.
echo FFmpeg est necessaire pour extraire les sous-titres depuis les videos.
echo Sans FFmpeg, seul le mode "Upload SRT" fonctionnera.
echo.
echo Voulez-vous telecharger FFmpeg automatiquement? (environ 80 MB)
echo.
set /p DOWNLOAD_CHOICE="Telecharger FFmpeg? (O/N): "

if /i "%DOWNLOAD_CHOICE%"=="O" (
    echo.
    python setup_ffmpeg.py
    if %errorlevel% equ 0 (
        set "FFMPEG_PATH=%LOCAL_FFMPEG%"
        set "FFPROBE_PATH=%LOCAL_FFPROBE%"
    ) else (
        echo.
        echo Echec du telechargement. Continuer sans FFmpeg...
    )
) else (
    echo.
    echo Continuer sans FFmpeg. Seul le mode SRT fonctionnera.
)

:start_server
echo.
echo ========================================
echo  DoubleSub.io - Server de developpement
echo ========================================
echo.
echo Le site sera accessible sur: http://localhost:5000
echo.
echo Appuyez sur Ctrl+C pour arreter le serveur
echo.

venv\Scripts\python app.py

pause
