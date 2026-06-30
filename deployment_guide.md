# 设备检修知识检索与作业系统 — 部署文档

> **目标平台**: LoongArch 架构 CPU + 银河麒麟高级服务器操作系统 V10/V11  
> **比赛要求**: 软件需部署在自主指令系统 LoongArch 架构 + 银河麒麟高级服务器版上运行（不满足该要求视为0分）

---

## 一、环境要求

### 1.1 硬件要求

| 组件 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | LoongArch 4核 | LoongArch 8核 |
| 内存 | 8 GB | 16 GB（如需运行本地LLM） |
| 硬盘 | 256 GB | 512 GB |
| 网络 | 可选（本地模式离线运行） | 需要外网API连接（云端模式） |

### 1.2 操作系统

- **银河麒麟高级服务器操作系统 V10** 或 **V11** (LoongArch 版)
- 确认 LoongArch 架构: `uname -m` 应返回 `loongarch64` 或 `loongson`

### 1.3 软件依赖

| 软件 | 版本要求 | 安装方式 |
|------|---------|---------|
| Python | ≥ 3.10 | 系统包管理器或源码编译 |
| SQLite | 内置 | 无需单独安装 |
| Node.js | ≥ 18.x | 仅构建前端时需要，生产环境可只用 nginx 托管 `dist/` |
| Nginx | ≥ 1.20 | 可选，用于反向代理 |

---

## 二、银河麒麟/LoongArch 环境准备

### 2.1 确认操作系统和架构

```bash
# 确认架构
uname -m
# 应输出: loongarch64 或 loongson

# 确认系统版本
cat /etc/os-release
# 应包含: Kylin Linux Advanced Server

# 确认 CPU 信息
lscpu | grep "Architecture\|Model name"
```

### 2.2 安装 Python 环境

银河麒麟 V10 通常预装 Python 3，若版本过低可升级：

```bash
# 更新包管理器
sudo yum update -y   # 或 sudo apt update

# 安装 Python 3 和 pip
sudo yum install -y python3 python3-pip python3-devel
# 或 sudo apt install -y python3 python3-pip python3-dev

# 验证版本
python3 --version   # 应 ≥ 3.10
pip3 --version
```

### 2.3 安装构建工具

部分 Python 包需编译原生扩展，需 gcc 工具链：

```bash
sudo yum install -y gcc gcc-c++ make cmake
# 或 sudo apt install -y build-essential cmake
```

> **注意**: 在 LoongArch 上部分 pip 包可能没有预编译 wheel，需要源码编译。这可能会增加首次安装时间。

---

## 三、部署前安全检查

### 3.1 替换 JWT Secret Key

编辑 `backend/services/auth_service.py`:

```python
# 将第10行从:
SECRET_KEY = "your-secret-key-here-change-in-production"
# 改为从环境变量读取:
import os
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "fallback-key-change-me-immediately")
```

### 3.2 清理已提交的 API Key

由于 `.env` 已被 git 追踪，需要从仓库历史中移除：

```bash
# 从追踪中移除 .env（如果已提交）
git rm --cached backend/.env

# 在 .gitignore 中确认 .env 已在名单中
# 然后重新生成 .env，不要包含真实密钥
```

### 3.3 限制 CORS（生产环境）

编辑 `backend/main.py`:

```python
# 将 allow_origins=["*"] 改为:
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:4173", "http://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 3.4 设置安全环境变量

```bash
# 生成强随机 SECRET_KEY
openssl rand -hex 32
# 输出类似: a1b2c3d4e5f6... 复制此值

# 设置环境变量
export JWT_SECRET_KEY="你的强随机密钥"
export DEEPSEEK_API_KEY="你的真实API Key"
```

---

## 四、部署方式一：直接部署（推荐）

### 4.1 克隆/上传代码

```bash
# 如果使用 git（需确保仓库已清理 .env）
git clone <your-repo-url> /opt/device-maintenance
cd /opt/device-maintenance
```

### 4.2 后端部署

#### 4.2.1 创建虚拟环境并安装依赖

```bash
# 创建 Python 虚拟环境
cd /opt/device-maintenance/backend
python3 -m venv venv
source venv/bin/activate

# 升级 pip
pip install --upgrade pip

# 安装核心依赖
pip install -r requirements.txt

# 安装额外依赖（如需要语音/视频功能）
pip install opencv-python-headless SpeechRecognition

# 验证关键依赖可导入
python3 -c "from fastapi import FastAPI; print('FastAPI OK')"
python3 -c "from sqlalchemy import create_engine; print('SQLAlchemy OK')"
```

> ⚠️ 在 LoongArch 上，`pip install chromadb` 可能失败。如无法安装，删除 `requirements.txt` 中的 `chromadb` 行并移除相关导入——当前系统实际使用自研 TF-IDF 引擎，不依赖 ChromaDB。

#### 4.2.2 配置环境变量

创建 `backend/.env`（不要含真实 API Key！）：

```bash
DEBUG=false
PORT=8000
LLM_MODE=cloud
LLM_PROVIDER=deepseek
LLM_MODEL_NAME=deepseek-chat
QWEN_API_KEY=
DEEPSEEK_API_KEY=
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
OPENAI_API_KEY=
LOCAL_LLM_PATH=./models/qwen-7b-int4.gguf
JWT_SECRET_KEY=<your-generated-secret>
```

> 在生产环境或比赛演示环境中，建议通过系统环境变量而非 `.env` 文件传递 API Key：  
> `export DEEPSEEK_API_KEY="sk-xxx"`

#### 4.2.3 准备数据文件

```bash
# 确保数据目录存在
cd /opt/device-maintenance/backend
mkdir -p data/uploads data/images data/processed

# 如果有数据文件(dataxyy.json)，放到 data/processed/ 下
# 或复制根目录的 dataxyy.json
cp ../dataxyy.json data/processed/ 2>/dev/null || true
```

#### 4.2.4 启动后端服务

```bash
# 测试启动
cd /opt/device-maintenance/backend
source venv/bin/activate
python3 main.py

# 验证: 访问 http://<server-ip>:8000/health
# 应返回: {"code":200,"message":"ok","data":{"status":"healthy"}}
```

#### 4.2.5 配置 systemd 服务（生产级）

创建 `/etc/systemd/system/device-maintenance.service`:

```ini
[Unit]
Description=设备检修知识检索与作业系统 - Backend
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/device-maintenance/backend
EnvironmentFile=/opt/device-maintenance/backend/.env
ExecStart=/opt/device-maintenance/backend/venv/bin/python3 main.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

启用服务：

```bash
sudo systemctl daemon-reload
sudo systemctl enable device-maintenance
sudo systemctl start device-maintenance
sudo systemctl status device-maintenance
```

### 4.3 前端部署

#### 4.3.1 构建前端（在开发机或目标机上）

```bash
cd /opt/device-maintenance/frontend

# 安装 Node.js（如目标机没有，可在构建机上完成）
# 建议使用 nvm 安装 Node 18+
curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.0/install.sh | bash
source ~/.bashrc
nvm install 18

# 安装依赖并构建
npm install
npm run build

# 构建产物在 frontend/dist/ 目录
ls dist/
# 应包含: index.html, assets/ 等
```

#### 4.3.2 配置 API 地址

编辑前端 API 配置（如不通过 Nginx 代理）：

修改 `frontend/src/api/index.ts` 或构建时设置环境变量：

```typescript
// 构建时通过环境变量设置 API 地址
const API_BASE = import.meta.env.VITE_API_URL || '/api'
```

构建命令（带环境变量）：

```bash
VITE_API_URL=http://your-server-ip:8000 npm run build
```

或在 `frontend/vite.config.ts` 中修改代理目标：

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8000',  // 后端地址
      changeOrigin: true
    }
  }
}
```

#### 4.3.3 使用 Nginx 托管前端 + 反向代理后端

安装 Nginx：

```bash
sudo yum install -y nginx
# 或 sudo apt install -y nginx
```

编辑 `/etc/nginx/conf.d/device-maintenance.conf`:

```nginx
server {
    listen 80;
    server_name _;  # 或填实际域名/IP
    
    # 前端静态文件
    root /opt/device-maintenance/frontend/dist;
    index index.html;
    
    # SPA 路由处理（所有非 API 请求返回 index.html）
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    # API 反向代理到后端
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # 大文件上传支持
        client_max_body_size 100M;
        proxy_read_timeout 300s;
    }
}
```

启动 Nginx：

```bash
sudo nginx -t                        # 测试配置
sudo systemctl enable nginx
sudo systemctl start nginx
sudo systemctl status nginx
```

---

## 五、部署方式二：Docker 部署（推荐但需确认 LoongArch 兼容性）

> **注意**: Docker 在 LoongArch 上的支持取决于银河麒麟版本。KylinOS V10 SP3 开始支持 Docker。如系统不支持，请使用方式一。

### 5.1 安装 Docker

```bash
# 银河麒麟上安装 Docker
sudo yum install -y docker
sudo systemctl enable docker
sudo systemctl start docker

# 确认正常运行
docker --version
docker info | grep -i architecture  # 应显示 loongarch64
```

### 5.2 Dockerfile

创建项目根目录下的 `Dockerfile`:

```dockerfile
# ============================================
# 阶段一: 构建前端
# ============================================
FROM node:18-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ .
RUN npm run build

# ============================================
# 阶段二: 运行后端 + 服务前端
# ============================================
FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# 复制后端代码
COPY backend/ ./backend/
WORKDIR /app/backend

# 安装 Python 依赖（移除可能不兼容的 chromadb）
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir opencv-python-headless

# 复制前端构建产物
COPY --from=frontend-builder /app/frontend/dist /usr/share/nginx/html/

# 复制 Nginx 配置
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

# 创建数据目录
RUN mkdir -p /app/backend/data/uploads /app/backend/data/images /app/backend/data/processed

# 暴露端口
EXPOSE 80

# 启动脚本
COPY docker/start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]
```

### 5.3 docker-compose.yml

```yaml
version: '3.8'

services:
  app:
    build: .
    container_name: device-maintenance
    ports:
      - "80:80"
    environment:
      - DEBUG=false
      - LLM_MODE=${LLM_MODE:-cloud}
      - LLM_PROVIDER=${LLM_PROVIDER:-deepseek}
      - LLM_MODEL_NAME=${LLM_MODEL_NAME:-deepseek-chat}
      - DEEPSEEK_API_KEY=${DEEPSEEK_API_KEY}
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
    volumes:
      - ./backend/data:/app/backend/data
      - ./dataxyy.json:/app/backend/data/processed/dataxyy.json:ro
    restart: always
```

### 5.4 构建和运行

```bash
# 创建 docker 配置目录
mkdir -p docker

# 创建 nginx.conf → docker/nginx.conf
# 创建 start.sh → docker/start.sh（见下方）

# 构建镜像
docker compose build

# 用环境变量文件运行
cat > .env.docker << 'EOF'
LLM_MODE=cloud
LLM_PROVIDER=deepseek
DEEPSEEK_API_KEY=sk-your-key-here
JWT_SECRET_KEY=your-strong-secret-key
EOF

docker compose --env-file .env.docker up -d

# 查看日志
docker compose logs -f
```

### 5.5 docker/nginx.conf

```nginx
server {
    listen 80;
    
    root /usr/share/nginx/html;
    index index.html;
    
    location / {
        try_files $uri $uri/ /index.html;
    }
    
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        client_max_body_size 100M;
        proxy_read_timeout 300s;
    }
}
```

### 5.6 docker/start.sh

```bash
#!/bin/bash

# 启动后端
cd /app/backend
python3 main.py &
BACKEND_PID=$!

# 启动 Nginx
nginx -g "daemon off;" &
NGINX_PID=$!

# 优雅退出
trap "kill $BACKEND_PID $NGINX_PID" EXIT

# 等待任意一个进程退出
wait -n
```

---

## 六、大模型配置

### 6.1 云端模式（推荐比赛演示）

```bash
# 在 .env 中配置
LLM_MODE=cloud
LLM_PROVIDER=deepseek  # 或 qwen, openai
LLM_MODEL_NAME=deepseek-chat  # 或 qwen-plus, gpt-4o-mini
DEEPSEEK_API_KEY=sk-your-key-here
```

### 6.2 本地模式（离线演示）

```bash
# 需要下载 GGUF 模型文件
# 如 Qwen2-7B-Instruct-GGUF 或 DeepSeek-R1-Distill-Qwen-7B-GGUF

mkdir -p backend/models

# 下载模型（示例：使用 huggingface-cli 或直接 wget）
# 注意 LoongArch 上的推理框架兼容性

LLM_MODE=local
LOCAL_LLM_PATH=./models/qwen-7b-int4.gguf
```

> ⚠️ **本地模型在 LoongArch 上的限制**:  
> - llama.cpp 需要 LoongArch 交叉编译支持  
> - GGUF 模型在 LoongArch 上的推理速度可能较慢  
> - **建议比赛演示优先使用云端模式**

### 6.3 混合模式

```bash
LLM_MODE=hybrid
# 简单问题用本地（快速），复杂问题用云端（精准）
```

---

## 七、验证部署

### 7.1 后端健康检查

```bash
# 直接启动时
curl http://localhost:8000/health
# 预期: {"code":200,"message":"ok","data":{"status":"healthy"}}

# 通过 Nginx 代理
curl http://localhost/api/health
```

### 7.2 前端验证

```bash
# 通过 Nginx 访问
curl http://localhost/
# 应返回 index.html 内容
```

浏览器访问 `http://<server-ip>`:

1. ✅ 首页显示"欢迎使用设备检修知识检索与作业系统"
2. ✅ 搜索页面可用
3. ✅ 注册/登录功能正常
4. ✅ AI 对话功能正常
5. ✅ 检修方案生成正常

---

## 八、性能调优

### 8.1 后端

```bash
# 使用 gunicorn 多 worker（生产环境）
pip install gunicorn
gunicorn main:app \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120
```

### 8.2 Nginx

在 `nginx.conf` 中添加性能优化：

```nginx
# gzip 压缩
gzip on;
gzip_types text/plain text/css application/json application/javascript image/svg+xml;
gzip_min_length 1000;

# 静态文件缓存
location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
    expires 30d;
    add_header Cache-Control "public, immutable";
}
```

---

## 九、常见问题排查

| 问题 | 可能原因 | 解决方案 |
|------|---------|---------|
| `sqlite3.OperationalError` | 数据库文件权限 | `chmod 755 backend/data/` |
| ModuleNotFoundError: `cv2` | 未安装 OpenCV | `pip install opencv-python-headless` |
| 前端访问 API 404 | Nginx 代理配置错误 | 检查 `location /api/` 配置 |
| `langchain` 相关导入错误 | 版本兼容 | `pip install langchain==0.1.10 langchain-openai==0.1.0` |
| ChromaDB 安装失败 | LoongArch 无预编译包 | 删除 chromadb 依赖，使用自研向量引擎 |
| 语音识别不可用 | 缺少 `SpeechRecognition` 或离线 | 安装库或用文字输入替代 |
| 视频分析不可用 | 缺少 `opencv-python` | 安装后重启 |
| CORS 错误 | 前端/后端跨域 | 检查 `main.py` 中 `allow_origins` |

---

## 十、部署检查清单

| 项目 | 完成 | 备注 |
|------|------|------|
| LoongArch 架构确认 | ☐ | `uname -m` → loongarch64 |
| 银河麒麟版本确认 | ☐ | `cat /etc/os-release` |
| Python 3.10+ 已安装 | ☐ | |
| 依赖已安装 (requirements.txt) | ☐ | 注意 chromadb 可能需跳过 |
| JWT SECRET_KEY 已替换 | ☐ | 不能使用默认值 |
| API Key 已配置 | ☐ | 通过环境变量传递 |
| CORS 已限制 | ☐ | 生产环境不能全开 |
| 数据文件已就位 | ☐ | data/processed/ |
| 前端已构建 | ☐ | dist/ 存在 |
| Nginx 已配置 | ☐ | SPA 路由 + API 代理 |
| 后端可访问 | ☐ | `/health` 返回正常 |
| 前端可访问 | ☐ | 首页正常显示 |
| 检索功能正常 | ☐ | 输入关键词可返回结果 |
| 登录/注册正常 | ☐ | |
| LLM 连接正常 | ☐ | AI 对话可回复 |
| 教师群验证提交 | ☐ | 确认满足评分要求 |

---

## 十一、附：LoongArch + 银河麒麟特殊注意事项

### 11.1 pip 源配置

银河麒麟可能无法直接访问 PyPI，建议配置国内镜像：

```bash
pip config set global.index-url https://mirrors.ustc.edu.cn/pypi/web/simple
# 或清华源
pip config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple
```

### 11.2 yum 源配置

如系统默认源失效，配置 KylinOS 官方源：

```bash
# 查看当前源
cat /etc/yum.repos.d/kylin_aarch64.repo

# 如需要，从龙芯或麒麟社区获取 LoongArch 专用源配置
```

### 11.3 NPM 源配置（前端构建时）

```bash
npm config set registry https://registry.npmmirror.com
```

### 11.4 确认 LoongArch 兼容性

比赛提供的云虚拟机应已预装好银河麒麟 + 基础工具链。如自行搭建：

- 确认 GCC 支持：`gcc --version`
- 确认 Python 支持：`python3 --version`
- 确认 Node.js 支持：`node --version`（如需前端构建）
