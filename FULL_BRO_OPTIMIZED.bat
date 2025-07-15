@echo off
cls
echo ========================================
echo     WHATSAPP EXTRACTOR - VERSION OPTIMISÉE
echo ========================================
echo.
echo Choisissez une option de traitement:
echo.
echo 1. TRANSCRIPTION INCRÉMENTALE (Recommandé)
echo    → Ne traite QUE les nouveaux fichiers
echo    → Garde toutes les transcriptions existantes
echo.
echo 2. Processus COMPLET (depuis le début)
echo    → Retraite TOUT (très long)
echo.
echo 3. EXPORT SIMPLE (2 colonnes: Contact / Messages)
echo.
echo 4. EXPORT STANDARD (4 fichiers CSV complexes)
echo.
echo 5. Diagnostic (vérifier l'état)
echo.
echo Q. Quitter
echo.

set /p choix=Votre choix (1-5, Q pour quitter): 

if /i "%choix%"=="Q" goto :fin

if "%choix%"=="1" (
    goto incremental
) else if "%choix%"=="2" (
    goto complet
) else if "%choix%"=="3" (
    goto export_simple
) else if "%choix%"=="4" (
    goto export_standard
) else if "%choix%"=="5" (
    goto diagnostic
) else (
    echo Option invalide!
    pause
    goto :eof
)

:incremental
echo.
echo ========================================
echo     TRANSCRIPTION INCRÉMENTALE (RECOMMANDÉ)
echo ========================================
echo.
echo Ce mode va:
echo   ✓ Garder TOUTES vos transcriptions existantes
echo   ✓ Ne transcrire QUE les nouveaux fichiers audio
echo   ✓ Être BEAUCOUP plus rapide
echo.
echo APPUYEZ SUR ENTRÉE POUR COMMENCER...
pause > nul

echo.
echo [1/2] Transcription des nouveaux fichiers...
python main.py --incremental --no-audio

echo.
echo [2/2] Génération des exports...
python main.py --simple-export --no-audio --no-transcription --incremental

goto fin

:complet
echo.
echo ========================================
echo     PROCESSUS COMPLET (OPTION 2)
echo ========================================
echo.
echo ⚠️  ATTENTION: Ce mode va TOUT retraiter depuis zéro!
echo    Cela peut prendre TRÈS longtemps (1h+)
echo.
echo Êtes-vous SÛR de vouloir continuer?
echo.
set /p confirm=Tapez OUI pour confirmer: 

if /i not "%confirm%"=="OUI" (
    echo Annulé.
    goto :eof
)

echo [1/1] Lancement du processus complet...
python main.py --full

goto fin

:export_simple
echo.
echo ========================================
echo     EXPORT SIMPLE (OPTION 3)
echo ========================================
echo.
echo Génération de l'export simple 2 colonnes...
echo.
pause

python main.py --simple-export --no-audio --no-transcription --incremental

goto fin

:export_standard
echo.
echo ========================================
echo     EXPORT STANDARD (OPTION 4)
echo ========================================
echo.
echo Génération des exports standards...
echo.
pause

if exist correction.py (
    python correction.py
)
python main.py --no-audio --no-transcription --incremental

goto fin

:diagnostic
echo.
echo ========================================
echo     DIAGNOSTIC
echo ========================================
echo.
echo Vérification de l'état du système...
echo.
pause

python diagnostic.py

echo.
echo Appuyez sur une touche pour continuer...
pause > nul

goto :eof

:fin
echo.
echo ========================================
echo           TERMINÉ !
echo ========================================
echo.

REM Détecter le dossier de sortie
if exist "C:\Users\Moham\Desktop\Data Leads" (
    set OUTPUT_DIR=C:\Users\Moham\Desktop\Data Leads
) else if exist "C:\Datalead3webidu13juillet" (
    set OUTPUT_DIR=C:\Datalead3webidu13juillet
) else (
    set OUTPUT_DIR=%CD%
)

echo Vos fichiers sont dans: %OUTPUT_DIR%
echo.

REM Vérifier quels fichiers ont été générés
echo FICHIERS GÉNÉRÉS:
echo -----------------

if exist "%OUTPUT_DIR%\export_simple.csv" (
    echo ✓ export_simple.csv - Format 2 colonnes simple
    echo ✓ export_simple.txt - Version texte
)

if exist "%OUTPUT_DIR%\export_simple.xlsx" (
    echo ✓ export_simple.xlsx - Version Excel
)

if exist "%OUTPUT_DIR%\messages_recus_only.csv" (
    echo ✓ messages_recus_only.csv - Messages reçus format complexe
)

if exist "%OUTPUT_DIR%\toutes_conversations_avec_transcriptions.txt" (
    echo ✓ toutes_conversations_avec_transcriptions.txt - Tout en texte
)

echo.
echo Appuyez sur une touche pour ouvrir le dossier...
pause > nul

explorer "%OUTPUT_DIR%"
