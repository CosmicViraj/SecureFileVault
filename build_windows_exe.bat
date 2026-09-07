@echo off
setlocal
cd /d "%~dp0"

echo ========================================
echo   Secure File Vault - Windows EXE Build
echo ========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo Python was not found in PATH.
    echo Install Python 3.11 or newer from python.org and enable "Add Python to PATH".
    pause
    exit /b 1
)

echo Installing/updating required packages...
python -m pip install --upgrade pip
if errorlevel 1 goto :error

python -m pip install cryptography pyinstaller
if errorlevel 1 goto :error

echo.
echo Building SecureFileVault.exe...
python -m PyInstaller --noconfirm --clean --onefile --windowed --name SecureFileVault secure_file_vault.py
if errorlevel 1 goto :error

echo.
echo Build complete.
echo Your EXE is here:
echo %~dp0dist\SecureFileVault.exe
start "" "%~dp0dist"
pause
exit /b 0

:error
echo.
echo Build failed. Review the error messages above.
pause
exit /b 1
