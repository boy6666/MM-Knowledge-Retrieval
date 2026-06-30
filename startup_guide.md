# 系统启动指南

需要按顺序启动 4 个服务。

---

## ① PostgreSQL

> 确保数据库已运行，AI Core 和 Java 后端都依赖它。

```powershell
# 管理员 PowerShell 运行
net start postgresql-x64-18
```

验证：

```
psql -h 127.0.0.1 -U postgres -d motor_maintenance -c "SELECT 1"
```
密码：`1234`，返回 `1` 即正常。

---

## ② AI Core（端口 8001）

> Python AI 微服务。

```bash
# 打开一个 CMD / PowerShell
conda activate mm-ai
cd ai-core
python main.py
```

看到以下输出即成功：

```
[AICore] 启动完成
INFO:     Uvicorn running on http://0.0.0.0:8001
```

验证：浏览器打开 http://localhost:8001/health

---

## ③ Java 后端（端口 8080）

> Spring Boot 主后端。

```bash
# 打开第二个 CMD / PowerShell
cd backend-java
mvnw spring-boot:run
```

首次启动会下载 Maven 依赖（较慢），看到以下输出即成功：

```
Started RepairApplication in 12.345 seconds
```

验证：浏览器打开 http://localhost:8080/health

---

## ④ 前端（端口 3000）

> Vue 3 开发服务器。

```bash
# 打开第三个 CMD / PowerShell
cd frontend
npx vite
```

看到以下输出即成功：

```
VITE v5.x  ready in xxx ms
➜  Local:   http://localhost:3000/
```

浏览器打开 **http://localhost:3000** 即可使用。

---

## 端口一览

| 服务 | 端口 | 健康检查地址 |
|------|------|-------------|
| PostgreSQL | 5432 | — |
| AI Core | 8001 | http://localhost:8001/health |
| Java 后端 | 8080 | http://localhost:8080/health |
| 前端 | 3000 | http://localhost:3000 |

---

## 常见问题

### Q: Java 启动报错 `java' 不是内部命令`

确认 JDK 已装：

```bash
java -version
java version "1.8.0_xxx"
```

### Q: `mvnw spring-boot:run` 找不到命令

```bash
dir backend-java\mvnw.cmd
```
确认文件存在，然后：

```bash
cd backend-java
mvnw.cmd spring-boot:run
```

### Q: AI Core 启动报错 `ModuleNotFoundError`

```bash
conda activate mm-ai
pip install -r ai-core/requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### Q: PostgreSQL 连不上

```powershell
# 管理员 PowerShell
net start postgresql-x64-18
```

### 停止所有服务

每个窗口按 `Ctrl+C` 停掉，或：

```bash
taskkill /f /im python.exe
taskkill /f /im java.exe
taskkill /f /im node.exe
```
