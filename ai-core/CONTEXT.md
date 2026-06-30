# AI/LLM 核心服务上下文

> 负责人：AI 组 | 技术栈：Python 微服务 + PostgreSQL + AGE + pgvector

---

## 一、架构定位

### 系统层级

```
┌──────────────────────────────────────────────┐
│           Java 后端 (Spring Boot)              │
│   ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│   │ 业务逻辑  │ │ 路由编排  │ │ 认证/权限    │ │
│   └─────┬────┘ └─────┬────┘ └──────┬───────┘ │
└─────────┼─────────────┼────────────┼──────────┘
          │ gRPC        │ HTTP       │ JDBC
          ▼             ▼            ▼
┌──────────────────────────────────────────────┐
│       Python AI 微服务 (你的范围)               │
│                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │ 检索引擎  │ │ 视频分析  │ │ 知识图谱操作  │ │
│  │ BGE-zh   │ │ YOLO+VL  │ │ AGE Cypher   │ │
│  │ AGE查询   │ │ 条件抽帧  │ │ 案例自动挂载  │ │
│  └──────────┘ └──────────┘ └──────────────┘ │
│                                              │
│  ┌──────────┐ ┌──────────┐ ┌──────────────┐ │
│  │ 语音服务  │ │ LLM调度   │ │ 对话管理     │ │
│  │ Sherpa   │ │ DeepSeek │ │ PostgreSQL   │ │
│  │ Edge-TTS │ │ Qwen API │ │ 持久化       │ │
│  └──────────┘ └──────────┘ └──────────────┘ │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────┴───────────────────────┐
│     PostgreSQL (龙芯 + 银河麒麟)               │
│                                              │
│  Apache AGE  ← 知识图谱 (设备/零件/步骤/案例)  │
│  pgvector    ← BGE 向量 (1024维)              │
│  业务表       ← 对话/案例/日志                 │
└──────────────────────────────────────────────┘
```

**龙芯上实际跑的内容：** PostgreSQL + AGE + pgvector 只此三项  
**AI 计算：** 走云端 API 或开发机，不部署在龙芯本地

---

## 二、已确认决策记录

| 编号 | 问题 | 决策 | 原因 |
|------|------|------|------|
| D01 | Java 迁移后 AI 服务形式 | **保留 Python 微服务**，Java 后端通过 gRPC 调用 | Python 的 LLM/向量/AGE 生态远强于 Java |
| D02 | 知识图谱技术栈 | **PostgreSQL + Apache AGE** | 统一数据库、图查询用 Cypher、与 pgvector 共享 PG |
| D03 | 视觉多模态模型 | **Qwen2.5-VL API（云端）**，不本地部署 | 8GB 本地跑不动 3B 模型，走 API 免费额度充足 |
| D04 | 文本 Embedding 模型 | **BAAI/bge-base-zh-v1.5**（CPU，~400MB） | bge-m3 (2.2GB) 在 8GB 上太挤，base 版够用 |
| D05 | 图 Embedding（Chinese-CLIP） | **去掉**，由 Qwen2.5-VL API 统一处理图文理解 | CLIP 已一年多未更新，Qwen-VL 能替代并更强 |
| D06 | YOLO 目标检测 | **保留 YOLOv8n ONNX（6MB）**，去掉 v8s | 8GB CPU 只能跑一个小模型，nano 版已够用 |
| D07 | YOLO 用途 | 零件检测 + 工具合规校验 | 缺陷检测暂不加入，等确定场景再补充 |
| D08 | 视频分析方式 | **条件触发 + 异步 Workers** | 见第三节详细设计 |
| D09 | 语音转文字 | **Sherpa-ONNX**（C++，跨平台，~50MB） | FunASR 依赖 PyTorch，LoongArch 不可编译 |
| D10 | 文字转语音 | **Edge-TTS**（云端免费 API） | 零部署成本，中文效果好 |
| D11 | 大模型兜底 | **DeepSeek / Qwen API**（云端） | 已有 API Key，直接复用 |
| D12 | 对话持久化 | **PostgreSQL 同一数据库** | 不另起 Redis / MongoDB，AI 微服务和 Java 后端共用 |
| D13 | LLM 模式 | **保留 hybrid**（本地 + 云端混合调度） | 竞赛亮点，云端为主，本地为离线备选 |
| D14 | AI 推理部署位置 | **云端 API + 开发机**，龙芯只跑 PostgreSQL | 8GB LoongArch 跑不动 PyTorch/ONNX 推理集群 |

---

## 三、视频分析详细设计

### 3.1 触发方式（非固定抽帧）

```
视频流 (30fps)
   │
   ├── [条件A] 画面差分 > 阈值
   │   └─ OpenCV 帧差分检测 → 有变化才抓帧
   │
   ├── [条件B] 工人语音提问
   │   └─ Sherpa-ONNX 实时识别 → 触发关键帧捕获
   │
   └── [条件C] 工人手动截图
       └─ 类似微信"拍照"按钮
              │
              ▼
        帧 Buffer (最近 10 帧)
              │
              ▼
    ┌──────────────────────┐
    │  异步 Worker 池       │ ← 最多同时 2 个任务
    │                       │
    │  Worker 1: YOLOv8n    │ ← 零件检测 (CPU, ~300ms)
    │   └─ 检测到新零件 →    │
    │      触发 Worker 2     │
    │                       │
    │  Worker 2: Qwen2.5-VL │ ← 理解画面 (API, ~2s)
    │      + AGE 图谱查询    │ ← 匹配步骤 (PG, ~50ms)
    └──────────────────────┘
              │
              ▼
      Edge-TTS 语音播报 + 文字提示
```

### 3.2 异步 Worker 策略

- **Worker 1 (YOLO)**: 一直运行，低优先级，检测到新零件才激活 Worker 2
- **Worker 2 (Qwen-VL + AGE)**: 按需启动，调用云端 API 不占本地 CPU
- **帧 Buffer**: 保留最近 10 帧，新帧到来时丢弃最旧帧
- **节流**: 同一零件的 Qwen 分析 30 秒内不重复触发

### 3.3 演示方案

竞赛演示时：
- 用**预录维修视频**代替实时摄像头
- 代码逐帧喂给系统，展示"自动识别 → 推送步骤"闭环
- 预录保证 100% 成功率，现场不会翻车

---

## 四、赛题需求 vs 实现对照

| 赛题需求 | 实现方式 | 状态 |
|---------|---------|------|
| B/S 架构 | 非 AI 组负责 | — |
| LoongArch + 银河麒麟 | PG + AGE + pgvector 在龙芯上跑，AI 走云端 | ✅ |
| 多模态知识检索（文本+图片+型号） | BGE-zh + Qwen2.5-VL API + AGE | ✅ |
| 精准语义检索 | BGE-base-zh-v1.5 向量化 + pgvector 检索 | ✅ |
| 跨模态匹配 | Qwen2.5-VL 统一处理图文理解 | ✅ |
| 标准化作业指引 | AGE Cypher 遍历步骤链 → 逐步推送 | ✅ |
| 合规校验提醒 | YOLOv8n 检测工具 → 对比 AGE 图谱要求 | ✅ |
| 个性化流程推送 | AGE 查询按设备类型+检修等级筛选 | ✅ |
| 知识沉淀（用户上传） | 案例 → 自动挂载 AGE 图谱 | ✅ |
| 知识审核 | AGE 图谱节点加 status 字段控制可见性 | ✅ |
| 手动标注修正 LLM 输出 | 案例编辑 → 更新图谱节点内容 | ✅ |

---

## 五、技术栈清单

### 5.1 Python AI 微服务

| 能力 | 组件 | 部署 | 内存 |
|------|------|------|------|
| 文本向量化 | BGE-base-zh-v1.5 | 本地 CPU | ~400MB |
| 图片理解 | Qwen2.5-VL API | 云端 API | 0 |
| 对话兜底 | DeepSeek / Qwen API | 云端 API | 0 |
| 零件检测 | YOLOv8n ONNX | 本地 CPU | ~100MB |
| 语音转文字 | Sherpa-ONNX | 本地 CPU | ~50MB |
| 语音播报 | Edge-TTS | 云端 API | 0 |
| 视频分析 | 条件触发 + 异步 Workers | 本地 + 云端 | ~200MB |

### 5.2 数据库（龙芯上）

| 组件 | 用途 | 内存预算 |
|------|------|---------|
| PostgreSQL 16 | 业务表 + pgvector | ~1GB |
| Apache AGE | 知识图谱 | ~200MB |
| pgvector | 向量存储与检索 (1024维) | ~300MB |

### 5.3 总内存预算

| 组件 | 内存 |
|------|------|
| PostgreSQL + AGE + pgvector | ~1.5GB |
| Python AI 微服务 | ~800MB |
| YOLOv8n (推理时) | ~100MB |
| Sherpa-ONNX (推理时) | ~50MB |
| 系统 + 其他 | ~2GB |
| **预留** | **~3.5GB** |
| **总计 8GB** | ✅ 可行 |

---

## 六、当前代码 vs 目标差距

| 模块 | 当前 | 目标 | 工作量 |
|------|------|------|--------|
| 向量检索 | 自研 TF-IDF（单字分词） | BGE-base-zh-v1.5 + pgvector | 中 |
| 图片检索 | 文字标签匹配 | Qwen2.5-VL 图文理解 | 中 |
| 知识图谱 | ❌ 不存在 | AGE Cypher 冷启动（你已写好） | 大（首批） |
| 案例挂载 | ❌ 不存在 | NLP + AGE 自动关联 | 中 |
| YOLO 零件检测 | ❌ 不存在 | YOLOv8n ONNX 推理 | 中 |
| 语音转文字 | ❌ 不存在（依赖未装） | Sherpa-ONNX 集成 | 中 |
| 视频分析 | ❌ 不存在 | 条件抽帧 + 异步 Workers | 大 |
| 工具合规 | ❌ 不存在 | YOLO + AGE 比对 | 中 |
| 对话持久化 | 内存级，重启丢失 | PostgreSQL 表存储 | 小 |
| 流式输出 (SSE) | ❌ 不支持 | FastAPI StreamingResponse | 小 |
| RAG 来源引用 | ❌ 无引用标注 | 检索结果附加 source | 小 |

---

## 七、目录结构（目标）

```
ai-core/
├── CONTEXT.md                    ← 本文件
├── llm/
│   ├── router.py                 ← LLM 调用路由 (hybrid)
│   ├── deepseek_adapter.py       ← DeepSeek API 封装
│   ├── qwen_adapter.py           ← Qwen/Qwen-VL API 封装
│   └── prompts/                  ← Prompt 模板
├── vector/
│   ├── embedder.py               ← BGE-base-zh-v1.5 封装
│   └── retriever.py              ← pgvector 检索引擎
├── knowledge_graph/
│   ├── age_client.py             ← AGE Cypher 查询封装
│   ├── cold_start.sql            ← 冷启动 Cypher 脚本
│   └── case_attacher.py          ← 案例自动挂载
├── vision/
│   ├── yolo_detector.py          ← YOLOv8n ONNX 推理
│   ├── frame_sampler.py          ← 条件抽帧
│   └── video_analyzer.py         ← 异步 Worker 池
├── speech/
│   ├── sherpa_stt.py             ← 语音转文字
│   └── edge_tts.py               ← 语音播报
├── conversation/
│   └── pg_store.py               ← 对话持久化 (PostgreSQL)
└── docker/
    ├── Dockerfile
    └── requirements.txt
```
