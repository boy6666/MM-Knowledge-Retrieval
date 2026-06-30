# Windows 启动指南

---

## 目录

- [1. 环境安装](#1-环境安装)
- [2. 配置文件](#2-配置文件)
- [3. 分步启动（推荐）](#3-分步启动推荐)
- [4. 一键启动](#4-一键启动)
- [5. 首次使用](#5-首次使用)
- [6. 停止服务](#6-停止服务)
- [7. 常见问题](#7-常见问题)

---

## 1. 环境安装

### 1.1 安装 Python

| 项目 | 说明 |
|------|------|
| 版本 | **Python 3.10 ~ 3.12**（推荐 3.11） |
| 下载 | [https://www.python.org/downloads/](https://www.python.org/downloads/) |
| 安装 | 打开安装包 → **勾选 ✅ "Add Python to PATH"** → Install Now |

安装完成后，打开命令提示符（CMD）验证：

```
python --version
pip --version
```

如果出现版本号，说明安装成功。

> ❓ **找不到 `python` 命令？**  
> 卸载重装 Python，务必勾选 "Add Python to PATH"，然后重启 CMD。

### 1.2 安装 Node.js

| 项目 | 说明 |
|------|------|
| 版本 | **Node.js 18.x 或 20.x**（LTS 版本） |
| 下载 | [https://nodejs.org/](https://nodejs.org/) → 左侧 LTS 版本 |

验证：

```
node --version
npm --version
```

---

## 2. 配置文件

用记事本打开 `backend/.env`，修改以下内容：

```ini
# 🌐 大模型模式（推荐用 cloud，不用装本地模型）
LLM_MODE=cloud
LLM_PROVIDER=deepseek

# 🔑 换成你自己的 Key（去 https://platform.deepseek.com 注册获取）
DEEPSEEK_API_KEY=sk-在这里粘贴你的key
```

其他配置保持默认不变。

> 💡 **没有 DeepSeek Key？** 也可以用其他模型：
> - 通义千问：`LLM_PROVIDER=qwen`，填入 `QWEN_API_KEY`
> - OpenAI：`LLM_PROVIDER=openai`，填入 `OPENAI_API_KEY`

---

## 3. 分步启动（推荐）

> 分步启动的好处是——每一步出了错能马上看到，方便排查。

### 3.1 启动后端

打开 **第一个 CMD 窗口**，依次执行：

```bash
# ① 进入后端目录
cd 你的项目路径\backend

# ② 创建虚拟环境（仅首次，执行一次即可）
python -m venv pyenv

# ③ 激活虚拟环境
pyenv\Scripts\activate

# ④ 安装依赖包（仅首次，等进度条跑完）
pip install -r requirements.txt

# ⑤ 启动后端服务（保持运行，不要关）
python main.py
```

看到以下输出说明启动成功：

```
[Main] 数据库初始化完成
INFO:     Uvicorn running on http://0.0.0.0:8000
```

✅ **验证**：浏览器打开 http://localhost:8000/health，看到返回 JSON 即为成功。

> ⚠️ **这个窗口不要关**，关了后端就停了。

### 3.2 启动前端

打开 **第二个 CMD 窗口**，依次执行：

```bash
# ① 进入前端目录
cd 你的项目路径\frontend

# ② 安装依赖（仅首次，等进度条跑完）
npm install

# ③ 启动前端（保持运行，不要关）
npx vite
```

看到以下输出说明启动成功：

```
VITE v5.x  ready in xxx ms
➜  Local:   http://localhost:3000/
```

> ⚠️ **这个窗口也不要关**，关了前端就停了。

### 3.3 打开浏览器

地址栏输入 **http://localhost:3000**，看到系统首页即部署完成。

---

## 4. 一键启动

如果你觉得开两个 CMD 麻烦，项目根目录已经有 `start_windows.bat`：

1. **双击** `start_windows.bat`
2. 它会自动创建虚拟环境、装依赖、启动后端和前端
3. 等几秒后浏览器打开 http://localhost:3000 即可

> ⚠️ 首次运行因为要下载依赖包，可能比较慢，等进度条跑完即可。

---

## 5. 首次使用

### 5.1 创建管理员账号

在 CMD 中执行：

```bash
cd backend
pyenv\Scripts\activate
python create_admin.py
```

### 5.2 创建测试用户

```bash
python create_test_user.py
```

### 5.3 默认账号

| 角色 | 用户名 | 密码 |
|------|--------|------|
| 管理员 | `admin` | `admin123` |
| 普通用户 | `user` | `user123` |

---

## 6. 停止服务

有两种方式：

### 方式一：按 Ctrl+C

分别切换到两个 CMD 窗口，各按一次 `Ctrl+C`。

### 方式二：使用停止脚本

双击 `stop_windows.bat`，一键杀掉所有 Python 和 Node 进程。

---

## 7. 常见问题

### pip 安装太慢怎么办？

```bash
# 加 -i 参数指定国内镜像
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### npm install 太慢怎么办？

```bash
# 指定国内镜像
npm install --registry=https://registry.npmmirror.com
```

### 端口被占用怎么办？

| 症状 | 原因 | 解决 |
|------|------|------|
| 后端端口 8000 被占用 | 其他程序在用 | 修改 `backend/.env` 把 `PORT=8000` 改成其他端口（如 8001） |
| 前端端口 3000 被占用 | 其他程序在用 | Vite 会自动跳到下一个端口（会在 CMD 里告诉你） |

### 前端页面白屏或报错

先检查后端 CMD 窗口是不是还活着。后端没启动时前端拿不到数据就会白屏。

### 登录报错 401

用默认账号：`admin` / `admin123`。

### 出现 `ModuleNotFoundError` 缺少某个包

```bash
# 重新安装依赖
cd backend
pyenv\Scripts\activate
pip install -r requirements.txt
```

---

## 附：目录结构说明

```
项目根目录/
├── start_windows.bat          ← 一键启动（双击）
├── stop_windows.bat           ← 一键停止（双击）
├── backend/
│   ├── main.py                ← 后端入口
│   ├── .env                   ← 配置文件（API Key 在这里填）
│   ├── requirements.txt       ← Python 依赖清单
│   ├── pyenv/                 ← 虚拟环境（自动创建，不用管）
│   └── data/
│       ├── app.db             ← 数据库文件
│       └── images/            ← 图片资源
├── frontend/
│   ├── package.json           ← 前端依赖清单
│   ├── node_modules/          ← 依赖包（自动下载，不用管）
│   └── src/                   ← 前端源码
```
