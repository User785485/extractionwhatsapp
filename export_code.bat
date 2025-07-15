@echo off
setlocal EnableDelayedExpansion

echo =========================================
echo Exportation du code source vers un fichier texte
echo =========================================

set OUTPUT_FILE=code_complet_whatsapp_extractor.txt
set PROJECT_DIR=%~dp0

echo Création du fichier %OUTPUT_FILE%...
echo WHATSAPP EXTRACTOR V2 - CODE SOURCE COMPLET > "%PROJECT_DIR%%OUTPUT_FILE%"
echo Généré le %date% à %time% >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo ========================================= >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"

echo Parcours des fichiers Python...

for /r "%PROJECT_DIR%" %%f in (*.py) do (
    echo Ajout du fichier: %%f
    echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
    echo ========================================= >> "%PROJECT_DIR%%OUTPUT_FILE%"
    echo FICHIER: %%f >> "%PROJECT_DIR%%OUTPUT_FILE%"
    echo ========================================= >> "%PROJECT_DIR%%OUTPUT_FILE%"
    echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
    type "%%f" >> "%PROJECT_DIR%%OUTPUT_FILE%"
    echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
    echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
)

echo Ajout des fichiers batch...

for /r "%PROJECT_DIR%" %%f in (*.bat) do (
    if not "%%~nxf"=="export_code.bat" (
        echo Ajout du fichier: %%f
        echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
        echo ========================================= >> "%PROJECT_DIR%%OUTPUT_FILE%"
        echo FICHIER: %%f >> "%PROJECT_DIR%%OUTPUT_FILE%"
        echo ========================================= >> "%PROJECT_DIR%%OUTPUT_FILE%"
        echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
        type "%%f" >> "%PROJECT_DIR%%OUTPUT_FILE%"
        echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
        echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
    )
)

echo Ajout des fichiers de configuration...

for /r "%PROJECT_DIR%" %%f in (*.ini, *.cfg, *.json) do (
    echo Ajout du fichier: %%f
    echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
    echo ========================================= >> "%PROJECT_DIR%%OUTPUT_FILE%"
    echo FICHIER: %%f >> "%PROJECT_DIR%%OUTPUT_FILE%"
    echo ========================================= >> "%PROJECT_DIR%%OUTPUT_FILE%"
    echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
    type "%%f" >> "%PROJECT_DIR%%OUTPUT_FILE%"
    echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
    echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
)

echo.
echo Exportation terminée !
echo Le code source a été compilé dans le fichier: %PROJECT_DIR%%OUTPUT_FILE%
echo.
echo Appuyez sur une touche pour quitter...
pause > nul
