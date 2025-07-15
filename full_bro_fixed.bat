@echo off
echo ========================================
echo WHATSAPP EXTRACTOR V2 - EXTRACTION COMPLETE
echo ========================================
echo.

REM Verifier que Python est installe
python --version >nul 2>&1
if errorlevel 1 (
    echo ERREUR: Python n'est pas installe ou n'est pas dans le PATH
    pause
    exit /b 1
)

echo Etape 1/6: Nettoyage des anciens fichiers...
if exist "C:\Datalead3webidu13juillet\toutes_conversations_avec_transcriptions.txt" (
    del "C:\Datalead3webidu13juillet\toutes_conversations_avec_transcriptions.txt"
)
if exist "C:\Datalead3webidu13juillet\messages_recus_avec_transcriptions.txt" (
    del "C:\Datalead3webidu13juillet\messages_recus_avec_transcriptions.txt"
)

echo Etape 2/6: Lancement de l'extraction complete...
python main_enhanced.py --full

echo.
echo Etape 3/6: Pause pour stabiliser le systeme...
timeout /t 3 /nobreak >nul

echo Etape 4/6: Force la regeneration des fichiers fusionnes...
python main_enhanced.py --skip-extraction --skip-media --skip-audio --skip-transcription --force-merger

echo.
echo Etape 5/6: Verification des resultats...
python test_export.py

echo.
echo Etape 6/6: Ouverture du dossier de resultats...
start "" "C:\Datalead3webidu13juillet"

echo.
echo ========================================
echo EXTRACTION TERMINEE !
echo ========================================
echo.
echo Fichiers generes:
echo - toutes_conversations_avec_transcriptions.txt
echo - messages_recus_only.csv
echo - contacts_messages_simplifies.csv
echo.
pause
