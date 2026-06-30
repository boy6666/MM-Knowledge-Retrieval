# 设备检修知识检索与作业系统 — Windows 部署与启动指南

---

## 一、前置环境准备

### 1.1 安装 Python

| 要求 | 说明 |
|------|------|
| 版本 | Python **3.10 ~ 3.12**（推荐 3.11） |
| 下载 | [python.org](https://www.python.org/downloads/) |
| 安装 | ✅ 勾选 **"Add Python to PATH"** → 点击 Install Now |

验证安装：

```bash
python --version    # 应输出 Python 3.10.x 或更高
pip --version       # 应输出 pip 23.x 或更高
```

### 1.2 安装 Node.js

| 要求 | 说明 |
|------|------|
| 版本 | Node.js **18.x 或 20.x**（LTS 版本） |
| 下载 | [nodejs.org](https://nodejs.org/) 或 [nvm-windows](https://github.com/coreybutler/nvm-windows) |

验证安装：

```bash
node --version    # 应输出 v18.x.x 或 v20.x.x
npm --version     # 应输出 9.x 或 10.x
```

---

## 二、项目文件准备

### 2.1 目录结构确认

确保以下文件结构完整（仅列出关键文件）：

```
your-project-folder/
├── start_windows.bat          ← 一键启动脚本（本文创建）
├── stop_windows.bat           ← 一键停止脚本
├── backend/
│   ├── main.py
│   ├── config.py
│   ├── requirements.txt
│   ├── .env                   ← 配置文件（见下方）
│   ├── services/
│   ├── routers/
│   ├── models/
│   └── data/                  ← 启动时自动创建
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
└── .gitignore
```

### 2.2 配置环境变量

创建 `backend/.env`（如果不存在）：

```ini
# ===== 基本配置 =====
DEBUG=true
PORT=8000

# ===== 大模型配置 =====
# 可选模式: cloud / local / hybrid
LLM_MODE=cloud
LLM_PROVIDER=deepseek
LLM_MODEL_NAME=deepseek-chat

# DeepSeek API (推荐)
DEEPSEEK_API_KEY=sk-your-key-here
DEEPSEEK_API_BASE=https://api.deepseek.com/v1

# 通义千问 (备选)
# LLM_PROVIDER=qwen
# QWEN_API_KEY=sk-your-key-here
# QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1

# OpenAI (备选)
# LLM_PROVIDER=openai
# OPENAI_API_KEY=sk-your-key-here
# OPENAI_API_BASE=https://api.openai.com/v1

# ===== 本地模型 (hybrid/local 模式时使用) =====
LOCAL_LLM_PATH=./models/qwen-7b-int4.gguf

# ===== JWT 安全 =====
# 强烈建议随机生成: python -c "import os; print(os.urandom(32).hex())"
JWT_SECRET_KEY=
JWT_EXPIRE_MINUTES=30
```

---

## 三、一键启动（推荐）

### 3.1 使用 start_windows.bat

双击 **`start_windows.bat`**，或右键 → **以管理员身份运行**。

脚本会自动执行：

```
[1/3] 创建 Python 虚拟环境（首次）
[1/3] 安装后端依赖（首次）
[1/3] 启动后端服务 → 弹窗: http://localhost:8000
[2/3] 安装前端依赖（首次）
[2/3] 启动前端服务 → 弹窗: http://localhost:3000
[3/3] 检查生产构建
```

启动后会弹出 **两个命令行窗口**（后端 + 前端），**不要关闭它们**。

> ⚠️ 首次启动时间较长（需下载依赖包），耐心等待即可。

### 3.2 停止服务

双击 **`stop_windows.bat`**，或按 `Ctrl+C` 依次关闭两个命令行窗口。

---

## 四、手动分步启动（调试用）

### 4.1 后端

```bash
# 打开终端1
cd backend

# 创建虚拟环境（仅首次）
python -m venv pyenv

# 激活虚拟环境
pyenv\Scripts\activate

# 安装依赖（仅首次）
pip install -r requirements.txt

# 如果需要语音/视频功能，额外安装：
pip install opencv-python-headless SpeechRecognition

# 启动后端
python main.py
```

预期输出：

```
[Main] 数据库初始化完成
INFO:     Uvicorn running on http://0.0.0.0:8000
```

> 访问 http://localhost:8000/health 验证是否返回 `{"code":200,"message":"ok"}`

### 4.2 前端

```bash
# 打开终端2
cd frontend

# 安装依赖（仅首次）
npm install

# 启动开发服务器
npx vite
```

预期输出：

```
VITE v5.x  ready in xxx ms
➜  Local:   http://localhost:3000/
```

### 4.3 访问系统

打开浏览器 → **http://localhost:3000**

---

## 五、生产部署模式（Nginx / IIS）

如需在生产环境用单一端口部署前后端：

### 5.1 构建前端

```bash
cd frontend
npm run build
# 产物: frontend/dist/
```

### 5.2 方案 A：使用 Nginx（推荐）

下载 Nginx for Windows → [nginx.org/en/download.html](https://nginx.org/en/download.html)

编辑 `nginx.conf`:

```nginx
server {
    listen 80;
    server_name localhost;
    
    # 前端静态文件
    root C:/path/to/frontend/dist;
    index index.html;
    
    # SPA 路由
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API 代理到后端
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 100M;
        proxy_read_timeout 300s;
    }
}
```

启动：

```powershell
# 在 Nginx 目录下
start nginx
```

### 5.3 方案 B：使用 IIS

1. 打开 **IIS 管理器** → 添加网站
2. 物理路径指向 `frontend/dist`
3. 添加 URL 重写规则（用于 SPA 路由）：

```xml
<configuration>
  <system.webServer>
    <rewrite>
      <rules>
        <rule name="SPA Routes" stopProcessing="true">
          <match url=".*" />
          <conditions>
            <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
            <add input="{REQUEST_URI}" pattern="^/api/" negate="true" />
          </conditions>
          <action type="Rewrite" url="/" />
        </rule>
      </rules>
    </rewrite>
    <proxy>
      <proxy url="http://localhost:8000" httpVersion="1.1" />
    </proxy>
  </system.webServer>
</configuration>
```

### 5.4 方案 C：http-server（轻量）

```bash
# 全局安装 http-server
npm install -g http-server

# 构建前端
cd frontend && npm run build

# 启动后端（终端1）
cd ..\backend
pyenv\Scripts\activate && python main.py

# 启动静态服务器 + 代理（终端2）
http-server frontend/dist -p 8080 --proxy http://localhost:8000
```

访问 http://localhost:8080

---

## 六、首次使用

### 6.1 创建管理员账号

```bash
cd backend
pyenv\Scripts\activate
python create_admin.py
```

### 6.2 创建测试用户

```bash
python create_test_user.py
```

### 6.3 验证所有功能

| 功能 | 操作 | 预期结果 |
|------|------|---------|
| 注册 | 点击"注册"→填写信息 | 注册成功 |
| 登录 | 使用注册的账号登录 | 跳转到首页 |
| 知识检索 | 输入"发动机异响" | 返回相关文档 |
| 检修方案 | 选择设备+故障→生成 | 生成方案步骤 |
| AI 对话 | 打开 AI 助手→提问 | LLM 回复 |
| 社区 | 发帖→审核→展示 | 流程完整 |

---

## 七、常见问题（Windows 特有）

| 问题 | 原因 | 解决 |
|------|------|------|
| `python` 不是内部命令 | Python 未加入 PATH | 重新安装 Python，勾选 "Add to PATH" |
| `pip` 安装报 SSL 错误 | 公司网络 / VPN | `pip install -r requirements.txt --trusted-host pypi.org --trusted-host files.pythonhosted.org` |
| `npm install` 报错 | Node 版本过低 | `nvm install 18` 或升级 Node.js |
| 端口 8000 被占用 | 其他程序占用 | 修改 `.env` 中的 `PORT` 值 |
| 端口 3000 被占用 | 其他程序占用 | Vite 会自动找下一个可用端口（见控制台输出） |
| 前端访问 API 403/404 | 跨域/代理问题 | 确认 vite.config.ts 中 proxy 配置正确 |
| `bcrypt` 安装失败 | 缺少 C++ 编译工具 | `pip install bcrypt --no-build-isolation` |
| 汉字显示乱码 | 终端编码 | start_windows.bat 已包含 `chcp 65001` |
| 上传大文件超时 | 默认超时短 | 修改 `main.py` 中 `post_max_size` |

---

## 八、目录说明

```
backend/
├── data/
│   ├── app.db              ← SQLite 数据库（用户/方案/帖子）
│   ├── chroma_db/           ← ChromaDB 缓存（当前未使用）
│   ├── images/              ← 上传图片 + PDF 提取图片
│   ├── processed/           ← 结构化JSON数据
│   └── uploads/             ← 用户上传文档
├── pyenv/                   ← Python 虚拟环境（首次启动创建）
└── .env                     ← 密钥配置（勿分享）
```

---

## 九、快速参考

```bash
# 重启后端（无需重启前端）
cd backend
pyenv\Scripts\activate
python main.py                    # Ctrl+C 停止 → 再运行即可

# 清除数据库（从头开始）
del backend\data\app.db
# 或: python -c "from utils.db import init_db; init_db()"

# 重新处理 PDF 数据
cd backend
pyenv\Scripts\activate
python scripts/parse_pdf_to_dataxyy.py

# 查看 API 文档（后端运行后）
# 浏览器打开: http://localhost:8000/docs
```
