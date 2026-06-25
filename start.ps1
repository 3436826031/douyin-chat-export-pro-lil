# 抖音聊天记录导出工具 - 启动脚本
$projectDir = "D:\project\myproject\douyin-chat-export"
$uvicorn = "$projectDir\venv\Scripts\uvicorn.exe"

Write-Host "正在启动抖音聊天记录导出工具..." -ForegroundColor Green

# 检查虚拟环境
if (!(Test-Path $uvicorn)) {
    Write-Host "错误: 未找到虚拟环境，请先执行首次部署" -ForegroundColor Red
    exit 1
}

# 启动服务
Start-Process -FilePath $uvicorn -ArgumentList "backend.main:app","--host","127.0.0.1","--port","8000" -WorkingDirectory $projectDir -WindowStyle Hidden

# 等待服务启动
Start-Sleep -Seconds 3

# 检查服务状态
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "启动成功!" -ForegroundColor Green
        Write-Host ""
        Write-Host "聊天记录浏览: http://localhost:8000" -ForegroundColor Cyan
        Write-Host "控制面板:     http://localhost:8000/panel" -ForegroundColor Cyan
        Write-Host ""
        Write-Host "如需停止服务，运行 stop.ps1" -ForegroundColor Yellow
    }
} catch {
    Write-Host "启动失败，请检查日志" -ForegroundColor Red
}
