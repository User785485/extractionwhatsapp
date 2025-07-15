@echo off
cls
echo ========================================
echo     WHATSAPP EXTRACTOR - TOUT EN UN
echo ========================================
echo.
echo Ce script va faire TOUT automatiquement:
echo.
echo 1. Extraire les conversations HTML
echo 2. Organiser les medias
echo 3. Convertir les audios en MP3
echo 4. Transcrire avec OpenAI (15 fichiers max)
echo 5. Generer TOUS les CSV et exports
echo.
echo IMPORTANT: Nettoyez manuellement si besoin AVANT de lancer!
echo.
echo APPUYEZ SUR ENTREE POUR COMMENCER...
pause > nul

echo.
echo [1/5] Lancement du processus complet...
python main.py --limit 15 --full

echo.
echo ========================================
echo            TERMINE ! 
echo ========================================
echo.
echo Vos fichiers sont dans: C:\DataLeads\
echo.
echo FICHIERS IMPORTANTS:
echo - transcriptions_speciales.csv
echo - messages_recus_par_contact.csv  
echo - toutes_conversations_avec_transcriptions.txt
echo.
echo Appuyez sur une touche pour ouvrir le dossier...
pause > nul

explorer "C:\DataLeads"