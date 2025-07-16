@echo off
title Test Rapide - 5 Contacts iPhone
color 0E
cls

echo ===================================================
echo    TEST RAPIDE - 5 CONTACTS IPHONE
echo    Extraction et export CSV/JSON
echo ===================================================
echo.

cd /d "%~dp0\src"

echo Extraction en cours...
echo.

python -c "from parsers.mobiletrans_parser import MobileTransParser; from exporters.csv_exporter import CSVExporter; from exporters.json_exporter import JSONExporter; from pathlib import Path; parser = MobileTransParser(); csv_exp = CSVExporter(); json_exp = JSONExporter(); files = [r'C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp\+1 (418) 550-4053.html', r'C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp\+1 (438) 304-7483.html', r'C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp\+1 (469) 559-3176.html', r'C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp\+1 (514) 247-8786.html', r'C:\Users\Moham\Downloads\iPhone_20250605021808\WhatsApp\+1 (514) 473-2352.html']; messages = []; print('[EXTRACTION] 5 fichiers iPhone...'); [[messages.append({'contact': c, 'content': m.content, 'timestamp': m.timestamp.isoformat() if m.timestamp else '', 'direction': m.direction.value}) for m in msgs] for f in files if Path(f).exists() for c, msgs in parser.parse(Path(f)).items()]; print(f'[OK] {len(messages)} messages extraits'); out_dir = Path('../test_5_contacts'); out_dir.mkdir(exist_ok=True); csv_exp.export(messages, out_dir / 'messages.csv'); json_exp.export(messages, out_dir / 'messages.json'); print(f'[OK] Exports sauvegardes dans: {out_dir.absolute()}')"

echo.
echo Test termine!
echo.
pause

cd ..
exit