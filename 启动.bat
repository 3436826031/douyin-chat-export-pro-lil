@echo off
chcp 65001 >nul
title 抖音聊天记录导出工具

echo ========================================
echo   抖音聊天记录导出工具 - 启动中...
echo ========================================
echo.

cd /d D:\project\myproject\douyin-chat-export

echo [1/2] 启动后端服务...
start /b "" "venv\Scripts\uvicorn.exe" backend.main:app --host 127.0.0.1 --port 8000

echo [2/2] 等待服务就绪...
timeout /t 3 /nobreak >nul

echo.
echo ========================================
echo   启动成功!
echo ========================================
echo.
echo   聊天记录浏览: http://localhost:8000
echo   控制面板:     http://localhost:8000/panel
echo.
echo   按任意键打开浏览器...
pause >nul

start http://localhost:8000/panel
