@echo off
title Ignore this window, it is to start the launcher. If you only see this window, something went wrong.
cd /d "%~dp0"
python -c "import webview" >nul 2>&1
if errorlevel 1 (
    color 2
    echo Installing pywebview...
    python -m pip install "pywebview>=5.0"
    if errorlevel 1 (
        color 4
        echo Could not install pywebview. Please install it manually with the command: python -m pip install "pywebview>=5.0"
        pause
        exit /b 1
    )
)
python main.py --browser
if errorlevel 1 pause
