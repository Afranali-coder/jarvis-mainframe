@echo off
title JARVIS MAINFRAME LAUNCHER
color 0A
cls
echo ===================================================
echo [SYSTEM]: Verifying Offline Ollama AI Engine...
echo ===================================================
echo.

:: Background mein check karega agar ollama pehle se ready hai
tasklist /FI "IMAGENAME eq ollama.exe" 2>NUL | find /I /N "ollama.exe">NUL
if "%errorlevel%" neq "0" (
    echo [SYSTEM]: Launching background AI core engine...
    start /b ollama serve
    timeout /t 3 >nul
)

echo [SYSTEM]: Launching JARVIS Matrix Core Array...
echo.

:: Execute your master python app file
python app.py

if %errorlevel% neq 0 (
    echo.
    echo [ERROR]: Application failed to launch successfully.
    echo [HELP]: Verify dependencies: pip install eel ollama pyttsx3 psutil screen-brightness-control opencv-python pyautogui
    echo.
    pause
)
exit
