@echo off
chcp 65001 >nul
title 停止服务

echo 正在停止服务...
taskkill /f /im uvicorn.exe >nul 2>&1

if %errorlevel%==0 (
    echo 服务已停止
) else (
    echo 服务未在运行
)

pause
