@echo off
title WhatsApp Extractor v2 - Interface Intuitive
color 0A

echo ==================================================
echo    WhatsApp Extractor v2 - Interface Intuitive
echo    Extraction simple et rapide
echo ==================================================
echo.

cd /d "%~dp0"

echo Configuration de l'environnement Python...
set PYTHONPATH=%cd%\src;%PYTHONPATH%

echo.
echo Lancement de l'interface...
echo.

cd src
python gui/intuitive_main_window.py

if errorlevel 1 (
    echo.
    echo [ERREUR] L'interface a rencontre une erreur.
    echo.
    echo Solutions possibles:
    echo 1. Verifiez que Python est installe
    echo 2. Installez les dependances: pip install -r requirements.txt
    echo.
    pause
)

cd ..
exit