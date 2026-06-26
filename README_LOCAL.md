# 抖音聊天记录导出工具 - Pro版本

## 版本更新说明

### v2.0 Pro 更新内容

**新增功能：**

1. **全局搜索**
   - 可以一次性搜索所有会话的聊天记录
   - 左侧显示相关会话列表，右侧显示匹配消息
   - 支持关键词高亮显示

2. **聊天记录查看器**
   - 按日期查看：日历组件 + 日期列表，点击日历直接跳转
   - 图片查看：网格展示所有图片，点击放大
   - 视频查看：网格展示所有视频，点击播放
   - 语音查看：列表展示所有语音，可直接播放
   - 分享查看：展示所有分享的视频/商品卡片

3. **数据统计**
   - 消息趋势：折线图展示消息数量变化，支持按天/月/年切换
   - 发送统计：饼图展示双方消息比例
   - 消息类型：统计文字、表情、图片、视频等各类消息数量
   - 活跃时段：24小时消息分布柱状图

4. **会话导出**
   - 在聊天界面直接导出当前会话
   - 支持 JSONL/JSON 格式

5. **手机版页面**
   - 适配手机端的聊天列表界面
   - 仿抖音风格设计
   - 访问地址：http://localhost:8000/mobile

6. **启动脚本**
   - `start.bat` - 一键启动服务
   - `stop.bat` - 一键停止服务

---

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
| 手机版页面 | http://localhost:8000/mobile |
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
