@echo off
cd /d "%~dp0"
python -c "import webview" >nul 2>&1
if errorlevel 1 (
    echo Installing the embedded window dependency...
    python -m pip install "pywebview>=5.0"
    if errorlevel 1 (
        echo Could not install pywebview. Check your internet connection and Python pip setup.
        pause
        exit /b 1
    )
)
python main.py --browser
if errorlevel 1 pause
