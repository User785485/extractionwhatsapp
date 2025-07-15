@echo off
cls
echo ========================================
echo     WHATSAPP EXTRACTOR - TOUT EN UN
echo ========================================
echo.
echo Choisissez une option de traitement:
echo.
echo 1. Processus COMPLET (depuis le debut)
echo 2. Commencer a partir de la CONVERSION AUDIO
echo 3. Commencer a partir de la TRANSCRIPTION
echo 4. EXPORT STANDARD (4 fichiers CSV complexes)
echo 5. EXPORT SIMPLE (2 colonnes: Contact / Messages) [NOUVEAU]
echo.
echo Q. Quitter
echo.

set /p choix=Votre choix (1-5, Q pour quitter): 

if /i "%choix%"=="Q" goto :fin

if "%choix%"=="1" (
    goto complet
) else if "%choix%"=="2" (
    goto audio
) else if "%choix%"=="3" (
    goto transcription
) else if "%choix%"=="4" (
    goto export_standard
) else if "%choix%"=="5" (
    goto export_simple
) else (
    echo Option invalide!
    pause
    goto :eof
)

:complet
echo.
echo ========================================
echo     PROCESSUS COMPLET (OPTION 1)
echo ========================================
echo.
echo Ce processus va faire TOUT depuis le debut:
echo.
echo 1. Extraire les conversations HTML
echo 2. Organiser les medias
echo 3. Convertir les audios en MP3
echo 4. Transcrire avec OpenAI
echo 5. Generer les exports
echo.
echo APPUYEZ SUR ENTREE POUR COMMENCER...
pause > nul

echo [1/1] Lancement du processus complet...
python main.py --full

goto choix_export

:audio
echo.
echo ========================================
echo     COMMENCER PAR LA CONVERSION AUDIO (OPTION 2)
echo ========================================
echo.
echo Ce processus va sauter l'extraction et commencer directement a:
echo.
echo 1. Convertir les audios en MP3
echo 2. Transcrire avec OpenAI
echo 3. Generer les exports
echo.
echo APPUYEZ SUR ENTREE POUR COMMENCER...
pause > nul

echo [1/1] Lancement a partir de la conversion audio...
REM On doit d'abord charger les conversations depuis le registre
python main.py --incremental

goto choix_export

:transcription
echo.
echo ========================================
echo     COMMENCER PAR LA TRANSCRIPTION (OPTION 3)
echo ========================================
echo.
echo Ce processus va:
echo.
echo 1. Transcrire les audios MP3 existants avec OpenAI
echo 2. Generer les exports avec les transcriptions
echo.
echo APPUYEZ SUR ENTREE POUR COMMENCER...
pause > nul

echo [1/1] Lancement de la transcription...
python main.py --no-audio --incremental

goto choix_export

:export_standard
echo.
echo ========================================
echo     EXPORT STANDARD (OPTION 4)
echo ========================================
echo.
echo Generation des 4 fichiers CSV standards:
echo - messages_recus_only.csv (multi-colonnes)
echo - messages_all.csv (multi-colonnes)
echo - toutes_conversations_avec_transcriptions.txt
echo - messages_recus_par_contact.csv
echo.
echo APPUYEZ SUR ENTREE POUR COMMENCER...
pause > nul

echo [1/2] Correction des donnees si necessaire...
if exist correction.py (
    python correction.py
) else (
    echo [INFO] correction.py non trouve, on continue...
)

echo [2/2] Generation des exports standards...
python main.py --no-audio --no-transcription --incremental

goto fin

:export_simple
echo.
echo ========================================
echo     EXPORT SIMPLE (OPTION 5) - NOUVEAU
echo ========================================
echo.
echo Generation de 2 fichiers simples:
echo.
echo FICHIER 1: export_simple.csv
echo   Colonne A: Contact/Identifiant
echo   Colonne B: Messages recus + transcriptions
echo.
echo FICHIER 2: export_simple.txt
echo   Format texte du meme contenu
echo.
echo FICHIER 3: export_simple.xlsx (si Excel installe)
echo.
echo APPUYEZ SUR ENTREE POUR COMMENCER...
pause > nul

echo [1/1] Generation de l'export simple...
python main.py --simple-export --no-audio --no-transcription --incremental

goto fin

:choix_export
echo.
echo ========================================
echo     QUEL TYPE D'EXPORT VOULEZ-VOUS ?
echo ========================================
echo.
echo 1. Export SIMPLE (2 colonnes seulement) [RECOMMANDE]
echo 2. Export STANDARD (4 fichiers complexes)
echo 3. Les DEUX types d'export
echo.

set /p export_type=Votre choix (1-3): 

if "%export_type%"=="1" (
    echo.
    echo Generation de l'export SIMPLE...
    python main.py --simple-export --no-audio --no-transcription --incremental
) else if "%export_type%"=="2" (
    echo.
    echo Generation de l'export STANDARD...
    if exist correction.py python correction.py
    python main.py --no-audio --no-transcription --incremental
) else if "%export_type%"=="3" (
    echo.
    echo Generation des DEUX types d'export...
    python main.py --simple-export --no-audio --no-transcription --incremental
    if exist correction.py python correction.py
    python main.py --no-audio --no-transcription --incremental
) else (
    echo Option invalide!
    goto choix_export
)

:fin
echo.
echo ========================================
echo           TERMINE !
echo ========================================
echo.

REM Detecter le dossier de sortie
if exist "C:\Users\Moham\Desktop\Data Leads" (
    set OUTPUT_DIR=C:\Users\Moham\Desktop\Data Leads
) else if exist "C:\Datalead3webidu13juillet" (
    set OUTPUT_DIR=C:\Datalead3webidu13juillet
) else (
    set OUTPUT_DIR=%CD%
)

echo Vos fichiers sont dans: %OUTPUT_DIR%
echo.

REM Verifier quels fichiers ont ete generes
echo FICHIERS GENERES:
echo -----------------

if exist "%OUTPUT_DIR%\export_simple.csv" (
    echo [NOUVEAU] export_simple.csv - Format 2 colonnes simple
    echo [NOUVEAU] export_simple.txt - Version texte
)

if exist "%OUTPUT_DIR%\export_simple.xlsx" (
    echo [NOUVEAU] export_simple.xlsx - Version Excel
)

if exist "%OUTPUT_DIR%\messages_recus_only.csv" (
    echo messages_recus_only.csv - Messages recus format complexe
)

if exist "%OUTPUT_DIR%\messages_recus_par_contact.csv" (
    echo messages_recus_par_contact.csv - Par contact
)

if exist "%OUTPUT_DIR%\toutes_conversations_avec_transcriptions.txt" (
    echo toutes_conversations_avec_transcriptions.txt - Tout en texte
)

echo.
echo Appuyez sur une touche pour ouvrir le dossier...
pause > nul

explorer "%OUTPUT_DIR%"