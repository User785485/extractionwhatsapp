@echo off
cls
echo ========================================
echo     EXPORT ET MERGE DES TRANSCRIPTIONS
echo ========================================
echo.
echo Ce script va:
echo 1. Consolider tous les messages avec les transcriptions
echo 2. Generer tous les fichiers CSV
echo.
echo APPUYEZ SUR ENTREE POUR COMMENCER...
pause > nul

echo.
echo [1/3] Consolidation des messages avec transcriptions...
echo ========================================
python correction.py

echo.
echo [2/3] Generation des fichiers CSV...
echo ========================================
python main_enhanced.py --skip-extraction --skip-media --skip-audio --skip-transcription

echo.
echo [3/3] Verification des resultats...
echo ========================================
cd C:\Datalead3webidu13juillet

echo.
echo FICHIERS GENERES:
echo -----------------
if exist toutes_conversations_avec_transcriptions.txt (
    for %%A in (toutes_conversations_avec_transcriptions.txt) do echo - toutes_conversations_avec_transcriptions.txt : %%~zA octets
) else (
    echo - toutes_conversations_avec_transcriptions.txt : MANQUANT!
)

if exist messages_recus_avec_transcriptions.txt (
    for %%A in (messages_recus_avec_transcriptions.txt) do echo - messages_recus_avec_transcriptions.txt : %%~zA octets
) else (
    echo - messages_recus_avec_transcriptions.txt : MANQUANT!
)

if exist contacts_messages_simplifies.csv (
    for %%A in (contacts_messages_simplifies.csv) do echo - contacts_messages_simplifies.csv : %%~zA octets
) else (
    echo - contacts_messages_simplifies.csv : MANQUANT!
)

if exist messages_recus_only.csv (
    for %%A in (messages_recus_only.csv) do echo - messages_recus_only.csv : %%~zA octets
) else (
    echo - messages_recus_only.csv : MANQUANT!
)

echo.
echo ========================================
echo           TERMINE !
echo ========================================
echo.
echo Appuyez sur une touche pour ouvrir le dossier...
pause > nul

explorer C:\Datalead3webidu13juillet