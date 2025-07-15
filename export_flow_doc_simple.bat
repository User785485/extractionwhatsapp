@echo off
setlocal

echo =========================================
echo DOCUMENTATION DU FLUX D'EXPORTATION DE WHATSAPP EXTRACTOR
echo =========================================

set OUTPUT_FILE=flux_exportation_documentation.txt
set PROJECT_DIR=%~dp0

echo WHATSAPP EXTRACTOR V2 - DOCUMENTATION DU FLUX D'EXPORTATION > "%OUTPUT_FILE%"
echo Genere le %date% a %time% >> "%OUTPUT_FILE%"
echo ========================================= >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo INTRODUCTION ET VUE D'ENSEMBLE >> "%OUTPUT_FILE%"
echo ========================================= >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo Le flux d'exportation CSV fonctionne selon la sequence suivante: >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo 1. main_enhanced.py - Point d'entree principal >> "%OUTPUT_FILE%"
echo 2. exporters/merger.py - Fusion des transcriptions >> "%OUTPUT_FILE%"
echo 3. exporters/csv_exporter.py - Exportateur CSV classique >> "%OUTPUT_FILE%"
echo 4. exporters/robust_exporter.py - Exportateur robuste ameliore >> "%OUTPUT_FILE%"
echo 5. fix_export.py - Script correctif (maintenant integre) >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo ========================================= >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo FICHIERS PRINCIPAUX >> "%OUTPUT_FILE%"
echo ========================================= >> "%OUTPUT_FILE%"

echo Ajout de main_enhanced.py >> "%OUTPUT_FILE%"
echo ========================================= >> "%OUTPUT_FILE%"
type "%PROJECT_DIR%main_enhanced.py" >> "%OUTPUT_FILE%" 2>nul || echo Fichier non trouve >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo Ajout de exporters\robust_exporter.py >> "%OUTPUT_FILE%"
echo ========================================= >> "%OUTPUT_FILE%"
type "%PROJECT_DIR%exporters\robust_exporter.py" >> "%OUTPUT_FILE%" 2>nul || echo Fichier non trouve >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo Ajout de exporters\csv_exporter.py >> "%OUTPUT_FILE%"
echo ========================================= >> "%OUTPUT_FILE%"
type "%PROJECT_DIR%exporters\csv_exporter.py" >> "%OUTPUT_FILE%" 2>nul || echo Fichier non trouve >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo Ajout de exporters\merger.py >> "%OUTPUT_FILE%"
echo ========================================= >> "%OUTPUT_FILE%"
type "%PROJECT_DIR%exporters\merger.py" >> "%OUTPUT_FILE%" 2>nul || echo Fichier non trouve >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo Ajout de fix_export.py >> "%OUTPUT_FILE%"
echo ========================================= >> "%OUTPUT_FILE%"
type "%PROJECT_DIR%fix_export.py" >> "%OUTPUT_FILE%" 2>nul || echo Fichier non trouve >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo Ajout de diagnostic_export.py >> "%OUTPUT_FILE%"
echo ========================================= >> "%OUTPUT_FILE%"
type "%PROJECT_DIR%diagnostic_export.py" >> "%OUTPUT_FILE%" 2>nul || echo Fichier non trouve >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo RESUME DES POINTS IMPORTANTS >> "%OUTPUT_FILE%"
echo ========================================= >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo 1. L'exportateur robuste (robust_exporter.py) est le composant principal pour >> "%OUTPUT_FILE%"
echo    generer un export CSV complet avec tous les contacts et transcriptions. >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo 2. Structure du CSV simplifie: >> "%OUTPUT_FILE%"
echo    - Colonne A: Contact (prenom ou numero de telephone) >> "%OUTPUT_FILE%"
echo    - Colonne B: Messages recus (textes + transcriptions audio) >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"
echo 3. Les transcriptions sont collectees depuis plusieurs sources: >> "%OUTPUT_FILE%"
echo    - Fichiers JSON de mapping dans .transcription_mappings >> "%OUTPUT_FILE%"
echo    - Registre unifie >> "%OUTPUT_FILE%"
echo    - Fichiers .txt >> "%OUTPUT_FILE%"
echo. >> "%OUTPUT_FILE%"

echo Documentation terminee !
echo Le document a ete cree: %OUTPUT_FILE%
echo.
pause
