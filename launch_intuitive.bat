@echo off
title WhatsApp Extractor v2 - Interface Intuitive
echo.
echo ===============================================
echo   WhatsApp Extractor v2 - Interface Intuitive
echo   Base sur l'analyse de 30 utilisateurs
echo ===============================================
echo.

cd /d "%~dp0"

echo Lancement de l'interface intuitive...
python src/gui/intuitive_main_window.py

if errorlevel 1 (
    echo.
    echo ERREUR: Impossible de lancer l'interface intuitive
    echo.
    echo Solutions possibles:
    echo 1. Verifiez que Python est installe
    echo 2. Installez les dependances: pip install -r requirements.txt
    echo 3. Verifiez que le dossier src/ existe
    echo.
    pause
    exit /b 1
)

pause