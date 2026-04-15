@echo off
echo Building ShenaniganRanchInstaller.exe...
python -m PyInstaller --noconfirm --clean --onefile --windowed --name "ShenaniganRanchInstaller" installer.py
if %ERRORLEVEL% EQU 0 (
    echo.
    echo Build successful!
    echo EXE location: dist\ShenaniganRanchInstaller.exe
) else (
    echo.
    echo Build failed with error code %ERRORLEVEL%
)
pause
