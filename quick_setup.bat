@echo off
REM YouTube Transcripts - Quick Setup Script (Windows)
REM This script activates the virtual environment and runs setup.py

setlocal enabledelayedexpansion

set PROJECT_DIR=%~dp0
set VENV_DIR=%PROJECT_DIR%.venv

echo.
echo ╔════════════════════════════════════════════════════════════╗
echo ║   YouTube Transcripts - Quick Setup                       ║
echo ╚════════════════════════════════════════════════════════════╝
echo.

REM Check if venv exists
if not exist "%VENV_DIR%" (
    echo 📦 Virtual environment not found. Creating it...
    python -m venv "%VENV_DIR%"
    if errorlevel 1 (
        echo ❌ Failed to create virtual environment
        exit /b 1
    )
    echo ✅ Virtual environment created
    echo.
)

REM Activate venv
echo 🔄 Activating virtual environment...
call "%VENV_DIR%\Scripts\activate.bat"
if errorlevel 1 (
    echo ❌ Failed to activate virtual environment
    exit /b 1
)
echo ✅ Virtual environment activated
echo.

REM Check if setup.py exists
if not exist "%PROJECT_DIR%setup.py" (
    echo ❌ Error: setup.py not found in %PROJECT_DIR%
    exit /b 1
)

REM Run setup.py
echo 🚀 Running setup.py...
echo.
python "%PROJECT_DIR%setup.py" %*
if errorlevel 1 (
    echo ❌ Setup failed
    exit /b 1
)

echo.
echo ✅ Setup complete!
pause
