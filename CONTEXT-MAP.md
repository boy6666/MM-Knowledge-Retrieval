# CONTEXT-MAP

多上下文项目。本项目是一个设备检修知识检索与作业辅助系统，参加第十五届中国软件杯大赛。

## 上下文列表

| 上下文 | 路径 | 负责人 | 技术栈 |
|--------|------|--------|--------|
| 后端 (正在迁移) | `backend/CONTEXT.md` | 后端组 | FastAPI → Java Spring Boot |
| AI/LLM 核心服务 | `ai-core/CONTEXT.md` | AI 组 ← **你在这里** | Python + LLM API + 向量引擎 |
| 前端 | `frontend/CONTEXT.md` | 前端组 | Vue 3 + Element Plus + TypeScript |

## 跨上下文依赖

```
[前端] ──API 调用──▶ [后端] ──调用──▶ [AI 核心]
  │                                       │
  │                                 知识检索 / 方案生成 / 对话
  │                                       │
  └────── 图片/视频/语音上传 ──────▶ 多模态分析
```

## ADR 目录

架构决策记录：`docs/adr/`（按需创建）
