# AI Core API 接口文档

> Python AI 微服务对外接口  
> Java 后端通过 HTTP/gRPC 调用

---

## 通信方式

| 项目 | 说明 |
|------|------|
| 协议 | **HTTP REST** (开发阶段) / **gRPC** (生产) |
| 基础地址 | `http://localhost:8001` (可配置) |
| 数据格式 | JSON |
| 认证 | 无内部认证，由 Java 后端鉴权后转发 |

---

## 接口列表

### 1. 健康检查

```
GET /health
```

**响应:**

```json
{
  "status": "ok",
  "version": "1.0.0",
  "components": {
    "llm": true,
    "vector": true,
    "age": true,
    "yolo": false,
    "speech": false
  }
}
```

---

### 2. 知识检索

```
POST /api/v1/retrieve

Body:
{
  "query": "string",           // 用户查询文本
  "device_type": "string",     // 可选: 设备类型
  "top_k": 10,                 // 可选: 返回数量
  "include_images": true       // 可选: 是否包含图片
}
```

**响应:**

```json
{
  "query": "火花塞间隙是多少",
  "results": [
    {
      "type": "chunk",
      "chunk_id": "c0001",
      "title": "检查火花塞",
      "content": "用塞尺测量火花塞间隙a，超出范围须更换火花塞",
      "similarity": 0.92,
      "source": "维修手册",
      "page": 3,
      "images": [
        {
          "url": "/images/spark_plug_gap.jpg",
          "caption": "火花塞间隙测量示意图"
        }
      ]
    },
    {
      "type": "image",
      "chunk_id": "img0003",
      "title": "火花塞间隙示意图",
      "url": "/images/spark_plug_gap.jpg",
      "similarity": 0.85
    }
  ],
  "total": 15
}
```

---

### 3. 多模态检索（图片搜知识）

```
POST /api/v1/retrieve/image

Body: multipart/form-data
- image: File (图片文件)
- query: string (可选, 附加文字描述)
- top_k: int (可选, 默认10)
```

**响应:** (同检索接口)

```
{
  "query": "火花塞积碳",
  "analysis": "图片中火花塞电极有黑色积碳...",
  "results": [...],
  "total": 5
}
```

---

### 4. 标准化作业指引

```
POST /api/v1/guidance/workflow

Body:
{
  "part_name": "火花塞",        // 部件名称
  "device_type": "摩托车发动机",  // 可选
  "fault_type": "无法启动"       // 可选
}
```

**响应:**

```json
{
  "part_name": "火花塞",
  "workflow": [
    {
      "step": 1,
      "name": "拆卸火花塞",
      "type": "拆卸",
      "description": "1. 用尖嘴钳将高压帽拔出。2. 用火花塞专用套筒将火花塞拆下。",
      "tools": ["尖嘴钳", "火花塞专用套筒"],
      "params": [],
      "cautions": ["逆时针转动火花塞将其拆下"]
    },
    {
      "step": 2,
      "name": "检查火花塞",
      "type": "检查",
      "description": "检查火花塞电极状态，用塞尺测量间隙",
      "tools": ["塞尺"],
      "params": ["火花塞间隙: 0.7~0.9mm"],
      "cautions": []
    },
    {
      "step": 3,
      "name": "安装火花塞",
      "type": "安装",
      "description": "预紧3圈后再转1/4圈，或使用定扭扳手拧紧至20±2 N·m",
      "tools": ["火花塞专用套筒", "定扭扳手"],
      "params": ["拧紧力矩: 20±2 N·m"],
      "cautions": ["必须使用定扭扳手"]
    }
  ],
  "total_steps": 3,
  "estimated_time": "15分钟"
}
```

---

### 5. 故障案例查询

```
POST /api/v1/cases/search

Body:
{
  "query": "压缩压力过高",
  "device_type": "摩托车发动机",
  "page": 1,
  "page_size": 10
}
```

**响应:**

```json
{
  "total": 1,
  "items": [
    {
      "case_id": "CASE-001",
      "title": "发动机压缩压力过高——火花塞积碳",
      "equipment": "摩托车发动机-XXX型",
      "description": "启动困难，测量压缩压力为2100 kPa，超过标准值1900 kPa",
      "fault": "压缩压力过高",
      "cause": "火花塞积碳",
      "solution": "清除火花塞积碳",
      "images": ["/cases/images/case001_1.jpg"],
      "related_steps": ["检查火花塞", "测量压缩压力"],
      "technician": "张工",
      "date": "2024-01-15"
    }
  ]
}
```

---

### 6. 案例上传与挂载

```
POST /api/v1/cases/upload

Body:
{
  "title": "发动机异响——凸轮轴磨损",
  "equipment": "摩托车发动机-XXX型",
  "technician": "李工",
  "description": "发动机异响，拆检发现凸轮轴磨损",
  "process": "拆卸凸轮轴后发现凸轮面有磨损痕迹",
  "solution_detail": "更换凸轮轴，调整气门间隙",
  "fault_name": "凸轮轴磨损",
  "part_name": "凸轮轴",
  "param_name": "",
  "images": ["/cases/images/case002_1.jpg"]
}
```

**响应:**

```json
{
  "status": "ok",
  "case_id": "CASE-002",
  "message": "案例已挂载到知识图谱"
}
```

---

### 7. AI 对话

```
POST /api/v1/chat

Body:
{
  "conversation_id": "uuid",       // 已有对话ID，或空字符串创建新对话
  "user_id": 1,                    // 可选
  "message": "火花塞间隙多少",
  "media_type": "text",            // text / image / audio / video
  "media_url": "",                 // 媒体文件URL (图片/语音)
  "stream": false                  // 是否流式输出
}
```

**响应 (非流式):**

```json
{
  "conversation_id": "uuid",
  "response": "火花塞间隙标准值为0.7~0.9毫米...",
  "cited_sources": ["维修手册第3页"],
  "related_images": [
    {"url": "/images/spark_plug_gap.jpg", "caption": "火花塞间隙测量"}
  ],
  "provider": "deepseek",
  "difficulty": "low"
}
```

**响应 (流式, `stream: true`):** SSE (Server-Sent Events)

```
data: {"token": "火花"}
data: {"token": "塞"}
data: {"token": "间"}
data: {"token": "隙"}
data: {"token": "标"}
data: {"token": "准"}
data: {"token": "值"}
data: [DONE]
```

---

### 8. 语音转文字

```
POST /api/v1/speech/stt

Body: multipart/form-data
- audio: File (音频文件, 支持 wav/mp3/webm)
```

**响应:**

```json
{
  "text": "火花塞间隙是多少",
  "duration": 2.5
}
```

---

### 9. 文字转语音

```
POST /api/v1/speech/tts

Body:
{
  "text": "请用塞尺测量火花塞间隙，标准值0.7到0.9毫米",
  "lang": "zh-CN"
}
```

**响应:** 音频二进制流 (Content-Type: audio/mp3)

或 JSON:

```json
{
  "audio_url": "/audio/tts_xxx.mp3",
  "duration": 3.2
}
```

---

### 10. 图片分析 (Qwen2.5-VL)

```
POST /api/v1/vision/analyze

Body: multipart/form-data
- image: File (图片文件)
- prompt: string (可选, 分析提示, 默认"请描述这张图片中的设备状态和可能的故障")
```

**响应:**

```json
{
  "description": "图片中是一个火花塞，电极周围有黑色积碳...",
  "detected_parts": [
    {"label": "火花塞", "confidence": 0.95, "bbox": [100, 200, 300, 400]}
  ],
  "possible_faults": ["火花塞积碳", "电极磨损"],
  "suggestions": ["清除火花塞积碳", "检查火花塞间隙"]
}
```

---

### 11. 视频帧分析 (YOLO + Qwen-VL)

```
POST /api/v1/vision/video-frame

Body: multipart/form-data
- image: File (视频帧截图)
```

**响应:**

```json
{
  "parts": [
    {"label": "火花塞", "confidence": 0.95, "bbox": [100, 200, 300, 400]}
  ],
  "description": "画面中是一个火花塞拆卸工具",
  "workflow": [
    {"step": 1, "name": "拆卸火花塞", "type": "拆卸"}
  ],
  "voice_prompt": "请使用火花塞专用套筒拆卸火花塞"
}
```

---

### 12. 知识图谱查询 (AGE)

```
POST /api/v1/graph/query

Body:
{
  "cypher": "MATCH (p:部件 {name: '火花塞'})-[:包含]->(step) RETURN step"
}
```

**响应:**

```json
{
  "results": [...],
  "total": 4
}
```

> ⚠️ 此接口为底层透传，Java 组应优先使用上层的 `workflow` / `cases/search` 接口。

---

## 错误码

```json
{
  "error": {
    "code": "LLM_NOT_CONFIGURED",
    "message": "大模型 API Key 未配置"
  }
}
```

| 错误码 | HTTP 状态码 | 说明 |
|--------|-----------|------|
| `LLM_NOT_CONFIGURED` | 503 | API Key 未配置 |
| `MODEL_NOT_FOUND` | 404 | YOLO 模型文件不存在 |
| `DB_NOT_CONNECTED` | 503 | PostgreSQL 未连接 |
| `AGE_NOT_READY` | 503 | AGE 图未初始化 |
| `INVALID_IMAGE` | 400 | 图片格式不支持 |
| `AUDIO_TOO_LARGE` | 413 | 音频文件超过 10MB |
| `RATE_LIMITED` | 429 | 请求频率超限 |
| `INTERNAL_ERROR` | 500 | 内部错误 |

---

## 数据目录约定

AI 微服务和 Java 后端共享以下目录（可通过 NFS / 对象存储 互通）：

```
/data/
├── images/           ← 上传的图片 / 手册图片
├── uploads/          ← 用户上传文件
├── cases/            ← 案例图片
├── audio/            ← TTS 生成的音频文件
└── processed/        ← 结构化 JSON 数据
```

Java 后端上传文件到这些目录后，将 URL 传给 AI 微服务即可。
