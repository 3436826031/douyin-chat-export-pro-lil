# 抖音聊天记录导出工具 - 本地启动指南

## 环境要求

| 依赖 | 版本要求 |
|------|----------|
| Python | >= 3.10 |
| Node.js | >= 20.19 或 >= 22.12 |

## 首次部署

```powershell
# 进入项目目录
cd D:\project\myproject\douyin-chat-export

# 创建 Python 虚拟环境（使用 Python 3.13）
py -3.13 -m venv venv

# 激活虚拟环境
.\venv\Scripts\activate

# 安装 Python 依赖
pip install -r requirements.txt
playwright install chromium

# 构建前端
cd frontend
npm install
npm run build
cd ..

# 启动服务
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

## 日常启动

```powershell
# 进入项目目录
cd D:\project\myproject\douyin-chat-export

# 激活虚拟环境
.\venv\Scripts\activate

# 启动服务
uvicorn backend.main:app --host 127.0.0.1 --port 8000
```

## 后台启动（不占用终端）

```powershell
Start-Process -FilePath "D:\project\myproject\douyin-chat-export\venv\Scripts\uvicorn.exe" -ArgumentList "backend.main:app","--host","127.0.0.1","--port","8000" -WorkingDirectory "D:\project\myproject\douyin-chat-export" -WindowStyle Hidden
```

## 停止服务

```powershell
Stop-Process -Name uvicorn -Force
```

## 访问地址

| 页面 | 地址 |
|------|------|
| 聊天记录浏览 | http://localhost:8000 |
| 控制面板 | http://localhost:8000/panel |

## 使用流程

1. 打开控制面板 http://localhost:8000/panel
2. 登录抖音（扫码或导入 Cookie）
3. 点击"开始采集"导出聊天记录
4. 回到首页浏览聊天记录

## 常见问题

**Q: Python 版本不对怎么办？**

系统有多个 Python 版本时，使用 `py -3.13` 指定版本创建虚拟环境。

**Q: 前端修改后需要重新构建吗？**

是的，修改前端代码后需要重新执行：
```powershell
cd frontend
npm run build
cd ..
```

**Q: 数据存储在哪里？**

所有数据存储在 `data/` 目录下，包括数据库、浏览器配置、媒体文件等。
