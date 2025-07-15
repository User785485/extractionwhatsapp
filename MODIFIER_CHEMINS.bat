@echo off
cls
echo ========================================
echo     MODIFICATION DES CHEMINS WHATSAPP
echo ========================================
echo.
echo Ce script vous permet de modifier facilement
echo les chemins des fichiers HTML et media.
echo.
echo IMPORTANT: 
echo - Assurez-vous de connaître les chemins corrects
echo - Les modifications seront enregistrées dans config.ini
echo.
echo APPUYEZ SUR ENTREE POUR COMMENCER...
pause > nul

python modifier_chemins.py

echo.
echo ========================================
echo            TERMINE ! 
echo ========================================
