@echo off
title Test Extraction WhatsApp
color 0E

echo ==================================================
echo    Test Direct d'Extraction WhatsApp
echo    Fichiers iPhone selectionnes
echo ==================================================
echo.

cd /d "%~dp0\src"

echo Test avec 2 fichiers iPhone...
echo.

python -c "import sys; sys.path.insert(0, '.'); from parsers.mobiletrans_parser import MobileTransParser; from exporters.csv_exporter import CSVExporter; from pathlib import Path; parser = MobileTransParser(); files = [r'C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp\+1 (418) 550-4053.html', r'C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp\+1 (438) 304-7483.html']; print('[TEST] Debut du test...'); messages = []; [messages.extend([{'contact': c, 'msg': m.content[:50]} for m in msgs]) for f in files if Path(f).exists() for c, msgs in parser.parse(Path(f)).items()]; print(f'[OK] {len(messages)} messages extraits'); csv = CSVExporter(); out = Path('../test_rapide.csv'); csv.export(messages, out) if messages else None; print(f'[OK] Export: {out}' if messages else '[INFO] Aucun message')"

echo.
echo Test termine!
echo.

cd ..
pause