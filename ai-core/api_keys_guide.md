# API Key 申请清单

按优先级排序，先去申请最关键的。

---

## 必备（不申请系统跑不起来）

### ① DeepSeek API ← 主 LLM 对话

| 项目 | 说明 |
|------|------|
| 用途 | AI 对话、方案生成、大模型兜底 |
| 官网 | https://platform.deepseek.com |
| 注册 | 手机号注册 → 左边栏 "API Keys" → 创建 Key |
| 费用 | 注册送 500 万 tokens，够比赛用 |
| 拿到后填 | `ai-core/config/settings.py` 或 `.env` |
| 字段 | `DEEPSEEK_API_KEY` / `DEEPSEEK_API_BASE` |

### ② 通义千问 Dashscope API ← 图片理解 (Qwen2.5-VL)

| 项目 | 说明 |
|------|------|
| 用途 | 多模态检索的图片分析、视频帧理解 |
| 官网 | https://dashscope.aliyun.com |
| 注册 | 阿里云账号 → 开通 "模型服务" → 创建 API-KEY |
| 费用 | 新用户免费额度很大，VL 模型按量计费很便宜 |
| 拿到后填 | `QWEN_API_KEY` / `QWEN_API_BASE` |

---

## 建议申请（提升体验）

### ③ OpenAI API（备选）

| 项目 | 说明 |
|------|------|
| 用途 | 如果 DeepSeek 不稳定时的备用 LLM |
| 官网 | https://platform.openai.com |
| 费用 | 付费，先不急着申请 |
| 字段 | `OPENAI_API_KEY` / `OPENAI_API_BASE` |

---

## 不需要 Key 的（免费直接用）

| 服务 | 用途 | 方式 |
|------|------|------|
| **Edge-TTS** | 文字转语音播报 | `pip install edge-tts`，免费，无需 Key |
| **HuggingFace** | 下载 BGE 模型 | `huggingface-cli download BAAI/bge-base-zh-v1.5`，无需登录 |
| **Ultralytics** | 下载 YOLOv8n ONNX | 自动下载，无需 Key |

---

## 拿到 API Key 后往哪里填

创建 `ai-core/.env`：

```ini
# ===== LLM (必备) =====
DEEPSEEK_API_KEY=sk-你的deepseek-key
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# ===== 通义千问 (必备, 图片理解用) =====
QWEN_API_KEY=sk-你的dashscope-key
QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
QWEN_VL_MODEL=qwen-vl-plus

# ===== LLM 模式 =====
LLM_MODE=cloud

# ===== PostgreSQL (等装好再配) =====
PG_HOST=localhost
PG_PORT=5432
PG_DB=motor_maintenance
PG_USER=postgres
PG_PASSWORD=postgres

# ===== 模型路径 =====
EMBEDDING_MODEL_PATH=./models/bge-base-zh-v1.5
YOLO_MODEL_PATH=./models/yolov8n.onnx
```

---

## 总结

| # | 服务 | 是否必备 | 申请时间 | 预计到手 |
|---|------|---------|---------|---------|
| 1 | **DeepSeek API** | ✅ 必备 | 现在就去 | 5 分钟 |
| 2 | **Dashscope (Qwen-VL)** | ✅ 必备 | 现在就去 | 10 分钟 |
| 3 | OpenAI API | ⏸️ 备选 | 不急 | — |

**拿到这两个 Key 后告诉我，我开始装依赖和测试。**
