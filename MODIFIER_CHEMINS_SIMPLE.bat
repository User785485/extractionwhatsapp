@echo off
cls
echo ========================================
echo  MODIFICATION DES CHEMINS WHATSAPP
echo ========================================
echo.
echo Ce script vous permet de modifier facilement
echo les chemins des fichiers HTML et media.
echo.
echo Options disponibles:
echo   1) Afficher les chemins actuels
echo   2) Modifier le chemin HTML
echo   3) Modifier le chemin Media
echo   4) Modifier le chemin de sortie
echo   5) Quitter
echo.
echo ========================================
echo.

:MENU
set /p choix="Votre choix (1-5): "

if "%choix%"=="1" goto AFFICHER
if "%choix%"=="2" goto HTML
if "%choix%"=="3" goto MEDIA
if "%choix%"=="4" goto SORTIE
if "%choix%"=="5" goto FIN

echo Choix invalide, veuillez reessayer.
goto MENU

:AFFICHER
cls
echo Affichage des chemins actuels...
echo.
python afficher_chemins.py
echo.
pause
goto MENU

:HTML
cls
echo Modification du chemin HTML
echo.
set /p html="Nouveau chemin HTML: "
if "%html%"=="" goto MENU
python modifier_chemins_simple.py --html "%html%"
echo.
pause
goto MENU

:MEDIA
cls
echo Modification du chemin Media
echo.
set /p media="Nouveau chemin Media: "
if "%media%"=="" goto MENU
python modifier_chemins_simple.py --media "%media%"
echo.
pause
goto MENU

:SORTIE
cls
echo Modification du chemin de sortie
echo.
set /p sortie="Nouveau chemin de sortie: "
if "%sortie%"=="" goto MENU
python modifier_chemins_simple.py --output "%sortie%"
echo.
pause
goto MENU

:FIN
cls
echo ========================================
echo            AU REVOIR!
echo ========================================
