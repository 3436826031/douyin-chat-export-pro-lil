# 抖音聊天记录导出工具 - 停止脚本
Write-Host "正在停止服务..." -ForegroundColor Yellow

$process = Get-Process -Name uvicorn -ErrorAction SilentlyContinue
if ($process) {
    Stop-Process -Name uvicorn -Force
    Write-Host "服务已停止" -ForegroundColor Green
} else {
    Write-Host "服务未在运行" -ForegroundColor Gray
}
