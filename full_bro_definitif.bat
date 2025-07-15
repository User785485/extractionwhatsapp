@echo off
echo ========================================
echo WHATSAPP EXTRACTOR V2
echo ========================================

echo [1/4] Extraction complete...
python main_enhanced.py --full

echo [2/4] Recreation des fichiers globaux...
python final_fix.py

echo [3/4] Consolidation alternative...
python correction.py

echo [4/4] Generation des CSV...
python main_enhanced.py --skip-extraction --skip-media --skip-audio --skip-transcription

echo.
echo TERMINE!
pause
