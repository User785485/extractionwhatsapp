@echo off
echo === TEST 5 CONTACTS IPHONE ===
echo.

cd /d "%~dp0"

echo Test direct avec 5 fichiers selectionnes...
echo.

python -c "import sys; from pathlib import Path; sys.path.insert(0, str(Path('src'))); from parsers.mobiletrans_parser import MobileTransParser; from exporters.csv_exporter import CSVExporter; parser = MobileTransParser(); files = [r'C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp\+1 (418) 550-4053.html', r'C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp\+1 (438) 304-7483.html']; total = 0; print('[TEST] Parsing 2 fichiers...'); [print(f'[OK] {Path(f).name}: {len(list(parser.parse(Path(f)).values())[0]) if parser.validate_file(Path(f)) and parser.parse(Path(f)) else 0} messages') for f in files if Path(f).exists()]; print('[DONE] Test termine')"

echo.
echo Pour un test complet, lancez l'interface graphique:
echo python src/gui/intuitive_main_window.py
echo.
pause