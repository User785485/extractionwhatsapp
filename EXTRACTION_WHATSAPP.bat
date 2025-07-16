@echo off
title WhatsApp Extractor v2 - FONCTIONNEL
color 0A
cls

echo ========================================================
echo          WhatsApp Extractor v2 - VERSION CORRIGEE
echo          Extraction de vos conversations WhatsApp
echo ========================================================
echo.

cd /d "%~dp0\src"

echo [1] Interface graphique complete
echo [2] Test rapide avec 5 fichiers iPhone
echo [3] Verifier que tout fonctionne
echo.

set /p choice="Choisissez une option (1-3): "

if "%choice%"=="1" goto interface
if "%choice%"=="2" goto test_rapide
if "%choice%"=="3" goto test_complet

echo Option invalide!
pause
exit

:interface
echo.
echo Lancement de l'interface graphique...
python gui/intuitive_main_window.py
goto end

:test_rapide
echo.
echo Test rapide avec 5 fichiers...
python -c "from parsers.mobiletrans_parser import MobileTransParser; from exporters.csv_exporter import CSVExporter; from pathlib import Path; parser = MobileTransParser(); files = [r'C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp\+1 (418) 550-4053.html', r'C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp\+1 (438) 304-7483.html', r'C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp\+1 (469) 559-3176.html', r'C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp\+1 (514) 247-8786.html', r'C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp\+1 (514) 473-2352.html']; total_msgs = 0; print('\n[TEST] Extraction de 5 contacts iPhone...\n'); [print(f'[OK] {Path(f).name}: {len(list(parser.parse(Path(f)).values())[0]) if parser.parse(Path(f)) else 0} messages') or [total_msgs := total_msgs + len(list(parser.parse(Path(f)).values())[0])] for f in files if Path(f).exists()]; print(f'\n[TOTAL] {total_msgs} messages extraits')"
goto end

:test_complet
echo.
echo Test complet du systeme...
python test_imports.py
goto end

:end
echo.
echo.
pause
cd ..
exit