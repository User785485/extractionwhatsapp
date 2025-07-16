@echo off
title WhatsApp Extractor v2 - INTERFACE
color 0A
cls

echo ==================================================
echo    WhatsApp Extractor v2 - VERSION FONCTIONNELLE
echo    Extraction simple de vos conversations
echo ==================================================
echo.
echo Chargement de l'interface...
echo.

cd /d "%~dp0\src"

:: Lancer l'interface graphique
python gui/intuitive_main_window.py

if errorlevel 1 (
    echo.
    echo ===================================================
    echo ERREUR: L'interface n'a pas pu demarrer
    echo.
    echo Solutions:
    echo 1. Installez Python 3.8+ depuis python.org
    echo 2. Installez les dependances:
    echo    pip install beautifulsoup4 pandas openpyxl
    echo ===================================================
    pause
)

cd ..
exit