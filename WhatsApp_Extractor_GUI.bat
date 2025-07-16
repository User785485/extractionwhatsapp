@echo off
chcp 65001 >nul
title WhatsApp Extractor v2 - Lanceur Interface Graphique

echo ============================================================
echo   WhatsApp Extractor v2 - Interface Graphique
echo ============================================================
echo.

:: Vérifier si Python est installé
echo [1/4] Vérification de Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERREUR: Python n'est pas installé ou non accessible
    echo.
    echo Veuillez installer Python 3.8+ depuis https://python.org
    echo Assurez-vous de cocher "Add Python to PATH" lors de l'installation
    echo.
    pause
    exit /b 1
)

:: Afficher la version de Python
for /f "tokens=*" %%i in ('python --version 2^>^&1') do echo ✅ %%i détecté

:: Vérifier si pip est disponible
echo [2/4] Vérification de pip...
python -m pip --version >nul 2>&1
if errorlevel 1 (
    echo ❌ ERREUR: pip n'est pas disponible
    echo.
    pause
    exit /b 1
)
echo ✅ pip est disponible

:: Vérifier les dépendances critiques
echo [3/4] Vérification des dépendances...

:: Vérifier tkinter (normalement inclus avec Python)
python -c "import tkinter" >nul 2>&1
if errorlevel 1 (
    echo ❌ ERREUR: tkinter n'est pas disponible
    echo Tkinter est normalement inclus avec Python.
    echo Essayez de réinstaller Python avec l'option "tcl/tk and IDLE"
    echo.
    pause
    exit /b 1
)
echo ✅ tkinter disponible

:: Vérifier si les requirements sont installés
set "missing_deps=0"

python -c "import requests" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  requests manquant
    set "missing_deps=1"
)

python -c "import pydantic" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  pydantic manquant
    set "missing_deps=1"
)

python -c "import yaml" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  PyYAML manquant
    set "missing_deps=1"
)

python -c "import bs4" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  beautifulsoup4 manquant
    set "missing_deps=1"
)

:: Installer les dépendances manquantes si nécessaire
if "%missing_deps%"=="1" (
    echo.
    echo 📦 Installation des dépendances manquantes...
    echo Cela peut prendre quelques minutes...
    echo.
    
    python -m pip install --user requests pydantic PyYAML beautifulsoup4 rich click
    
    if errorlevel 1 (
        echo ❌ ERREUR: Impossible d'installer les dépendances
        echo.
        echo Solutions possibles:
        echo 1. Exécuter en tant qu'administrateur
        echo 2. Installer manuellement avec: pip install -r requirements.txt
        echo 3. Vérifier votre connexion internet
        echo.
        pause
        exit /b 1
    )
    
    echo ✅ Dépendances installées avec succès
) else (
    echo ✅ Toutes les dépendances sont disponibles
)

:: Vérifier que le fichier GUI existe
echo [4/4] Vérification de l'interface...
if not exist "src\gui\main_window.py" (
    echo ❌ ERREUR: Fichier d'interface introuvable
    echo.
    echo Le fichier src\gui\main_window.py est manquant.
    echo Assurez-vous d'être dans le bon dossier du projet.
    echo.
    pause
    exit /b 1
)
echo ✅ Interface graphique trouvée

echo.
echo ============================================================
echo   Lancement de l'interface graphique...
echo ============================================================
echo.

:: Changer vers le répertoire du script s'il ne l'est pas déjà
cd /d "%~dp0"

:: Lancer l'interface graphique
python src\gui\main_window.py

:: Vérifier si le lancement a réussi
if errorlevel 1 (
    echo.
    echo ❌ ERREUR: L'interface n'a pas pu démarrer
    echo.
    echo Détails de l'erreur ci-dessus.
    echo.
    echo Solutions possibles:
    echo 1. Vérifier les messages d'erreur
    echo 2. Relancer en tant qu'administrateur
    echo 3. Vérifier que Python est correctement installé
    echo 4. Consulter les logs dans le dossier logs/
    echo.
    pause
    exit /b 1
)

:: Si on arrive ici, l'application s'est fermée normalement
echo.
echo Application fermée.
pause