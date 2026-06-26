@echo off
chcp 65001 >nul
title DouyinChatExport

echo ========================================
echo   Starting...
echo ========================================
echo.

cd /d D:\project\myproject\douyin-chat-export

echo [1/2] Starting server...
start /b "" "venv\Scripts\uvicorn.exe" backend.main:app --host 127.0.0.1 --port 8000

echo [2/2] Waiting...
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   Success!
echo ========================================
echo.
echo   PC:   http://localhost:8000
echo   Phone: http://localhost:8000/mobile
echo   Panel: http://localhost:8000/panel
echo.
echo   Press any key to open browser...
pause >nul

start http://localhost:8000/panel
