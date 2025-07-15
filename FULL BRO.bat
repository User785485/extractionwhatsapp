@echo off
cls
echo ========================================
echo     WHATSAPP EXTRACTOR - TOUT EN UN
echo ========================================
echo.
echo Choisissez une option de traitement:
echo.
echo 1. Processus COMPLET (depuis le début)
echo 2. Commencer à partir de la CONVERSION AUDIO (sauter extraction)
echo 3. Commencer à partir de la TRANSCRIPTION (sauter extraction et conversion)
echo 4. Uniquement l'EXPORT (utiliser les transcriptions existantes)
echo.
echo Q. Quitter
echo.

set /p choix=Votre choix (1-4, Q pour quitter): 

if /i "%choix%"=="Q" goto :fin

if "%choix%"=="1" (
    goto complet
) else if "%choix%"=="2" (
    goto audio
) else if "%choix%"=="3" (
    goto transcription
) else if "%choix%"=="4" (
    goto export
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
echo Ce processus va faire TOUT depuis le début:
echo.
echo 1. Extraire les conversations HTML
echo 2. Organiser les medias
echo 3. Convertir les audios en MP3
echo 4. Transcrire avec OpenAI
echo 5. Générer TOUS les CSV et exports
echo.
echo APPUYEZ SUR ENTRÉE POUR COMMENCER...
pause > nul

echo [1/3] Lancement du processus complet...
python main_enhanced.py --full

echo [2/3] Reconstruction des fichiers globaux...
python correction.py

echo [3/3] Finalisation de l'export...
python main_enhanced.py --skip-extraction --skip-media --skip-audio --skip-transcription
goto fin

:audio
echo.
echo ========================================
echo     COMMENCER PAR LA CONVERSION AUDIO (OPTION 2)
echo ========================================
echo.
echo Ce processus va sauter l'extraction et commencer directement à:
echo.
echo 1. Convertir les audios en MP3
echo 2. Transcrire avec OpenAI
echo 3. Générer TOUS les CSV et exports
echo.
echo APPUYEZ SUR ENTRÉE POUR COMMENCER...
pause > nul

echo [1/3] Lancement du processus à partir de la conversion audio...
python main_enhanced.py --skip-extraction --skip-media

echo [2/3] Reconstruction des fichiers globaux...
python correction.py

echo [3/3] Finalisation de l'export...
python main_enhanced.py --skip-extraction --skip-media --skip-audio --skip-transcription
goto fin

:transcription
echo.
echo ========================================
echo     COMMENCER PAR LA TRANSCRIPTION (OPTION 3)
echo ========================================
echo.
echo Ce processus va:
echo.
echo 1. Transcrire les audios MP3 existants avec OpenAI
echo 2. Générer TOUS les CSV et exports avec les transcriptions
echo.
echo APPUYEZ SUR ENTRÉE POUR COMMENCER...
pause > nul

echo [1/3] Lancement de la transcription...
python main_enhanced.py --skip-extraction --skip-media --skip-audio

echo [2/3] Reconstruction des fichiers globaux...
python correction.py

echo [3/3] Finalisation de l'export...
python main_enhanced.py --skip-extraction --skip-media --skip-audio --skip-transcription
goto fin

:export
echo.
echo ========================================
echo     EXPORT UNIQUEMENT (OPTION 4)
echo ========================================
echo.
echo Ce processus va uniquement:
echo 1. Générer TOUS les CSV et exports avec les transcriptions existantes
echo.
echo APPUYEZ SUR ENTRÉE POUR COMMENCER...
pause > nul

echo [1/2] Reconstruction des fichiers globaux...
python correction.py

echo [2/2] Génération des exports CSV...
python main_enhanced.py --skip-extraction --skip-media --skip-audio --skip-transcription
goto fin

:fin
echo.
echo ========================================
echo           TERMINÉ !
echo ========================================
echo.
echo Vos fichiers sont dans: C:\Datalead3webidu13juillet\
echo.
echo FICHIERS IMPORTANTS:
echo - messages_recus_only.csv
echo - messages_recus_par_contact.csv  
echo - contacts_messages_simplifies.csv   [NOUVEL EXPORT SIMPLIFIÉ avec numéros/prénoms]
echo - toutes_conversations_avec_transcriptions.txt
echo.
echo Appuyez sur une touche pour ouvrir le dossier...
pause > nul

explorer "C:\Datalead3webidu13juillet"