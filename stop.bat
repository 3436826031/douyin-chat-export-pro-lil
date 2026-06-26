@echo off
chcp 65001 >nul
title StopServer

echo Stopping server...
taskkill /f /im uvicorn.exe >nul 2>&1

if %errorlevel%==0 (
    echo Server stopped
) else (
    echo Server not running
)

pause
