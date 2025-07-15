@echo off
setlocal EnableDelayedExpansion

echo =========================================
echo DOCUMENTATION DU FLUX D'EXPORTATION DE WHATSAPP EXTRACTOR
echo =========================================

set OUTPUT_FILE=flux_exportation_documentation.txt
set PROJECT_DIR=%~dp0

echo Création du document de flux d'exportation...
echo WHATSAPP EXTRACTOR V2 - DOCUMENTATION DU FLUX D'EXPORTATION > "%PROJECT_DIR%%OUTPUT_FILE%"
echo Généré le %date% à %time% >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo ========================================= >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"

REM Introduction avec explication du flux
echo INTRODUCTION ET VUE D'ENSEMBLE DU FLUX D'EXPORTATION >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo ========================================= >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo Le flux d'exportation CSV de WhatsApp Extractor fonctionne selon la séquence suivante: >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo 1. main_enhanced.py - Point d'entrée principal qui coordonne tout le processus >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    - Traite les arguments de ligne de commande >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    - Configure l'environnement et les répertoires >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    - Appelle séquentiellement les différents modules de traitement >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    - Gère l'exportation via différents exportateurs >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo 2. exporters/merger.py - Fusion des transcriptions audio avec les messages >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    - Collecte les transcriptions depuis différentes sources >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    - Les fusionne avec les fichiers audio correspondants >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    - Génère des fichiers fusionnés intermédiaires >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo 3. exporters/csv_exporter.py - Exportateur CSV classique >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    - Crée les exports CSV à partir des fichiers fusionnés >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    - A des limitations pour certains contacts >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo 4. exporters/robust_exporter.py - Notre exportateur robuste amélioré >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    - Fonctionne indépendamment des fichiers fusionnés >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    - Collecte TOUS les contacts, même ceux sans messages >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    - Collecte toutes les transcriptions de différentes sources >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    - Génère un CSV simplifié à deux colonnes (Contact + Messages reçus) >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    - S'intègre dans le pipeline principal >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo 5. fix_export.py - Script correctif pour l'export (maintenant intégré dans robust_exporter) >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    - Fonctionnalité désormais incluse dans l'exportateur robuste >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo SCHÉMA DU FLUX DE DONNÉES: >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo [Fichiers HTML] --extraction--> [Messages texte/audio] --transcription--> [Messages + Transcriptions] >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo                                                                               | >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo                                                                               v >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo [Exportateur Robuste] --> [CSV simplifié] (contacts_messages_simplifies.csv) >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo                 \----> [Excel] (si disponible) >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo ========================================= >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"

REM Ajouter le point d'entrée principal
echo POINT D'ENTRÉE PRINCIPAL: main_enhanced.py >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo ========================================= >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo Ce fichier est le point d'entrée principal qui orchestrate tout le processus d'extraction et d'export. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo Il appelle les différents exportateurs dans un ordre précis. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
if exist "%PROJECT_DIR%main_enhanced.py" (
    type "%PROJECT_DIR%main_enhanced.py" >> "%PROJECT_DIR%%OUTPUT_FILE%"
) else (
    echo Fichier non trouvé >> "%PROJECT_DIR%%OUTPUT_FILE%"
)
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"

REM Ajouter l'exportateur robuste
echo EXPORTATEUR ROBUSTE: exporters/robust_exporter.py >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo ========================================= >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo Cet exportateur est le coeur de la solution d'export CSV améliorée. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo Il collecte tous les contacts et leurs messages reçus (texte + transcriptions) >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo et génère un CSV simplifié à deux colonnes. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
if exist "%PROJECT_DIR%exporters\robust_exporter.py" (
    type "%PROJECT_DIR%exporters\robust_exporter.py" >> "%PROJECT_DIR%%OUTPUT_FILE%"
) else (
    echo Fichier non trouvé >> "%PROJECT_DIR%%OUTPUT_FILE%"
)
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"

REM Ajouter l'exportateur CSV standard
echo EXPORTATEUR CSV STANDARD: exporters/csv_exporter.py >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo ========================================= >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo Cet exportateur standard crée des fichiers CSV à partir des fichiers fusionnés. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo Il a certaines limitations, notamment l'absence de certains contacts. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
if exist "%PROJECT_DIR%exporters\csv_exporter.py" (
    type "%PROJECT_DIR%exporters\csv_exporter.py" >> "%PROJECT_DIR%%OUTPUT_FILE%"
) else (
    echo Fichier non trouvé >> "%PROJECT_DIR%%OUTPUT_FILE%"
)
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"

REM Ajouter le module de fusion des transcriptions
echo MODULE DE FUSION DES TRANSCRIPTIONS: exporters/merger.py >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo ========================================= >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo Ce module gère la fusion des transcriptions audio avec les messages. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo Il collecte les transcriptions de différentes sources et les associe aux fichiers audio. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
if exist "%PROJECT_DIR%exporters\merger.py" (
    type "%PROJECT_DIR%exporters\merger.py" >> "%PROJECT_DIR%%OUTPUT_FILE%"
) else (
    echo Fichier non trouvé >> "%PROJECT_DIR%%OUTPUT_FILE%"
)
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"

REM Ajouter le script fix_export.py
echo SCRIPT CORRECTIF D'EXPORT: fix_export.py >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo ========================================= >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo Ce script était utilisé pour corriger l'export CSV. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo Sa fonctionnalité a maintenant été intégrée dans l'exportateur robuste. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
if exist "%PROJECT_DIR%fix_export.py" (
    type "%PROJECT_DIR%fix_export.py" >> "%PROJECT_DIR%%OUTPUT_FILE%"
) else (
    echo Fichier non trouvé >> "%PROJECT_DIR%%OUTPUT_FILE%"
)
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"

REM Ajouter le script diagnostic_export.py
echo SCRIPT DE DIAGNOSTIC D'EXPORT: diagnostic_export.py >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo ========================================= >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo Ce script analyse les problèmes d'export CSV. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo Il a été utilisé pour identifier les problèmes avec les transcriptions. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
if exist "%PROJECT_DIR%diagnostic_export.py" (
    type "%PROJECT_DIR%diagnostic_export.py" >> "%PROJECT_DIR%%OUTPUT_FILE%"
) else (
    echo Fichier non trouvé >> "%PROJECT_DIR%%OUTPUT_FILE%"
)
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"

REM Configuration utilisée
echo FICHIER DE CONFIGURATION: config.ini >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo ========================================= >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo Ce fichier contient la configuration utilisée par l'application. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
if exist "%PROJECT_DIR%config.ini" (
    type "%PROJECT_DIR%config.ini" >> "%PROJECT_DIR%%OUTPUT_FILE%"
) else (
    echo Fichier non trouvé >> "%PROJECT_DIR%%OUTPUT_FILE%"
)
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"

REM Résumé final
echo RÉSUMÉ ET POINTS IMPORTANTS >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo ========================================= >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo 1. L'exportateur robuste (robust_exporter.py) est maintenant le composant principal pour >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    générer un export CSV complet avec tous les contacts et transcriptions. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo 2. Structure du CSV simplifié: >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    - Colonne A: Contact (prénom si disponible, sinon numéro de téléphone) >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    - Colonne B: Messages reçus (textes + transcriptions audio) >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo 3. Les transcriptions sont collectées depuis plusieurs sources: >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    - Fichiers JSON de mapping dans .transcription_mappings >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    - Registre unifié (objet et fichier JSON) >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    - Fichiers .txt legacy >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo 4. L'exportateur est intégré dans le pipeline principal (main_enhanced.py) >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    et s'exécute automatiquement avec tous les modes d'exécution. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo 5. Le fichier généré "contacts_messages_simplifies.csv" contient tous les contacts >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo    avec leurs messages reçus incluant les transcriptions audio. >> "%PROJECT_DIR%%OUTPUT_FILE%"
echo. >> "%PROJECT_DIR%%OUTPUT_FILE%"

echo.
echo Documentation du flux d'exportation terminée !
echo Le document a été créé: %PROJECT_DIR%%OUTPUT_FILE%
echo.
echo Appuyez sur une touche pour quitter...
pause > nul
