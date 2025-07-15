@echo off
echo ========================================
echo CORRECTION ET EXPORT FINAL
echo ========================================
echo.

echo [1/2] Application du correctif final...
python final_fix.py

echo.
echo [2/2] Generation des fichiers CSV...
python main_enhanced.py --skip-extraction --skip-media --skip-audio --skip-transcription

echo.
echo ========================================
echo           TERMINE !
echo ========================================
echo.
echo Appuyez sur une touche pour ouvrir le dossier...
pause > nul

explorer "C:\Datalead3webidu13juillet"
