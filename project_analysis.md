# 设备检修知识检索与作业系统 — 项目分析报告

> 第十五届中国软件杯大赛 · A1赛题  
> 出题企业：龙芯中科技术股份有限公司  
> 基于多模态大模型技术的设备检修知识检索与作业系统

---

## 一、项目架构总览

```
project-root/
├── backend/                         # FastAPI 后端
│   ├── main.py                      # 应用入口 + 路由注册
│   ├── config.py                    # 配置管理（环境变量驱动）
│   ├── .env                         # 敏感配置（已提交到仓库 — 风险）
│   ├── requirements.txt             # Python 依赖
│   ├── models/                      # SQLAlchemy 数据模型
│   │   ├── user.py                  # 用户模型
│   │   ├── task.py                  # 检修方案 + 社区帖子模型
│   │   └── knowledge.py             # 知识 + 文档模型
│   ├── routers/                     # API 路由层（8 个模块）
│   │   ├── auth.py                  # 注册 / 登录
│   │   ├── search.py                # 文本 / 图片 / 混合检索
│   │   ├── guidance.py              # 检修方案生成 / 保存 / 管理
│   │   ├── community.py             # 社区帖子 / 审核
│   │   ├── knowledge.py             # 知识库 / 文档上传
│   │   ├── profile.py               # 个人中心 / LLM 配置
│   │   ├── chat.py                  # 多模态对话 / 语音 / 视频
│   │   └── admin.py                 # 管理后台
│   ├── services/                    # 业务逻辑层
│   │   ├── auth_service.py          # JWT / 密码哈希
│   │   ├── llm_service.py           # LLM 多模型调度
│   │   ├── vector_service_v2.py     # 自研 TF-IDF 向量检索引擎
│   │   ├── vector_service.py        # V1 版向量检索（仍在引用）
│   │   ├── guidance_service.py      # 检修方案业务逻辑
│   │   ├── community_service.py     # 社区业务逻辑
│   │   ├── conversation_service.py  # 对话管理（内存级）
│   │   └── data_processor_v2.py     # PDF 版面解析 + 图文绑定
│   ├── schemas/                     # Pydantic 数据校验
│   ├── utils/
│   │   ├── db.py                    # SQLite 引擎 + 会话管理
│   │   └── response.py             # 统一响应格式
│   ├── data/                        # 数据目录（已 gitignore）
│   │   ├── app.db                   # SQLite 数据库
│   │   ├── chroma_db/               # ChromaDB 目录（未使用）
│   │   ├── processed/               # 结构化 JSON 数据
│   │   ├── images/                  # 提取的图片
│   │   └── uploads/                 # 用户上传文件
│   └── scripts/
│       └── parse_pdf_to_dataxyy.py  # PDF 解析脚本
├── frontend/                        # Vue 3 前端
│   ├── src/
│   │   ├── main.ts                  # 入口
│   │   ├── App.vue                  # 根组件
│   │   ├── api/index.ts             # Axios HTTP 客户端 + 全部 API 封装
│   │   ├── router/index.ts          # 13 个路由
│   │   ├── stores/user.ts           # Pinia 用户状态
│   │   ├── components/Layout.vue    # 侧边栏布局
│   │   ├── views/                   # 11 个页面组件
│   │   │   ├── Home.vue             # 首页仪表盘
│   │   │   ├── Chat.vue             # AI 对话（文字/图片/语音/视频）
│   │   │   ├── Search.vue           # 知识检索
│   │   │   ├── Guidance.vue         # 检修方案
│   │   │   ├── Community.vue        # 经验社区
│   │   │   ├── Knowledge.vue        # 知识管理
│   │   │   ├── KnowledgeDetail.vue  # 知识详情
│   │   │   ├── Profile.vue          # 个人中心
│   │   │   ├── Admin.vue            # 管理后台
│   │   │   ├── Login.vue            # 登录
│   │   │   └── Register.vue         # 注册
│   │   └── utils/format.ts          # 工具函数
│   ├── dist/                        # 构建产物
│   ├── vite.config.ts               # Vite 配置（含 API 代理）
│   └── package.json
├── architecture_report.md           # 已有架构报告
├── dataxyy.json                     # 制造数据（根目录冗余）
└── .gitignore
```

---

## 二、赛题需求映射矩阵

### 2.1 基本功能需求

| 赛题需求 | 当前实现状态 | 证据 |
|----------|-------------|------|
| **B/S 架构** | ✅ 完全满足 — FastAPI + Vue 3 | `main.py` 使用 FastAPI 框架，前端 Vue 3 + Vite |
| **LoongArch + 银河麒麟部署** | ❌ **未验证** — 无 Dockerfile / 无部署脚本 | 无 `Dockerfile`, 无 `.deploy/`, 无 cross-build 配置 |
| **本地/云端大模型服务** | ✅ 支持 — 本地 GGUF / Qwen / DeepSeek / OpenAI | `llm_service.py:27-55` 支持多 provider |
| **PC Web 可视化界面** | ✅ 完全满足 — Element Plus UI | `Layout.vue` + 11 个视图组件 |
| **多模态知识检索** | ⚠️ **部分满足** — 文本检索 OK, 图片检索仅基于文本描述, 非真正多模态 | `search.py` `/search/text`, `/search/image` |
| **标准化作业指引** | ✅ 基础满足 — LLM 生成检修方案 + 步骤化指引 | `guidance.py` + `guidance_service.py` |
| **个性化流程推送** | ⚠️ **弱实现** — 仅通过 device_type / fault_type 筛选 | `guidance_service.py:list_public_guidance()` |
| **知识沉淀与更新** | ✅ 满足 — 社区帖子 + 知识库 + 审核机制 | `knowledge.py` + `community.py` |
| **审核机制** | ✅ 完全满足 — 管理员审核帖子/知识 | `community.py` approve/reject 接口 |
| **知识图谱** | ❌ **缺少** — 未实现知识图谱, 仅 TF-IDF 向量检索 | 无知识图谱相关代码 |

### 2.2 非功能性需求

| 需求 | 状态 | 备注 |
|------|------|------|
| 界面美观 | ✅ 基本满足 | Element Plus, 但部分页面缺少侧边栏适配 |
| 开发文档完整 | ⚠️ **不完整** — 仅有 `architecture_report.md` | 需要提交 5 份正式文档 |
| 人机交互便捷 | ✅ 基本满足 | 路由守卫 + 登录流完整 |
| 易用性与稳定性 | ⚠️ **有隐患** — 无日志系统 / 无错误追踪 | |

### 2.3 文档要求

| 必需文档 | 状态 | 备注 |
|----------|------|------|
| 软件功能需求分析文档 | ❌ 缺失 | — |
| 软件功能设计文档 | ❌ 缺失 | `architecture_report.md` 部分覆盖但格式不符 |
| 软件产品说明书 | ❌ 缺失 | — |
| 软件功能测试报告 | ❌ 缺失 | — |
| 软件安装包及部署文档 | ❌ 缺失 | 本文档正在补充 |
| 软件源文件 | ✅ 已有 | 完整源码 |
| 软件功能演示 PPT | ❌ 缺失 | — |
| 功能演示视频(≤7min) | ❌ 缺失 | — |

---

## 三、项目约束

### 3.1 技术约束

1. **架构约束**: 必须采用 B/S 架构 ✅
2. **CPU/OS 约束**: 部署目标为 LoongArch 架构 CPU + 银河麒麟高级服务器操作系统 V10/V11 ❌（未验证）
3. **硬件约束**: ≥ 4核 CPU / ≥ 8GB 内存 / ≥ 256GB 硬盘 — 需确认
4. **依赖约束**: 以下依赖在 LoongArch + Kylin 上可能不可用：
   - `speech_recognition` — 依赖 Google API，离线环境不可用
   - `opencv-python` (cv2) — Chat.vue 用到，但未在 `requirements.txt` 列出
   - `chromadb` 0.4.24 — 需确认 LoongArch 兼容性
   - `langchain` 系列 — 纯 Python，通常可运行
5. **密码方案**: 当前使用 `sha256_crypt`（中等强度），赛题实际要求 `bcrypt`（已在 requirements.txt 声明但未使用）

### 3.2 安全约束

1. **JWT SECRET_KEY** 硬编码为 `"your-secret-key-here-change-in-production"` — **必须替换**
2. **DEEPSEEK_API_KEY** 明文存在 `.env` 中且 `.env` 已提交到仓库（`.gitignore` 排除但已追踪）— **安全风险**
3. **CORS** 允许所有来源 `allow_origins=["*"]` — 生产环境需限制
4. **SQLite** 不支持高并发 — 比赛环境可行，生产需迁移

### 3.3 数据约束

1. **向量检索**: 自研 TF-IDF 引擎，非专业向量数据库（ChromaDB 已安装但未使用）
2. **对话存储**: 内存级 `ConversationService` — 重启后丢失
3. **数据来源**: 当前仅使用 `dataxyy.json` 和 PDF 解析数据，未接入真实维修数据流

---

## 四、差距分析（Gap Analysis）

### 4.1 关键差距（影响评分的硬伤）

| 编号 | 问题 | 严重性 | 影响评分项 | 说明 |
|------|------|--------|-----------|------|
| G1 | **LoongArch/Kylin 部署未验证** | 🔴 致命 | 基本功能(0分条款) | 不满足"软件需部署在自主指令系统LoongArch架构+银河麒麟高级服务器版上运行(不满足该要求视为0分)" |
| G2 | **缺少竞赛规定的 5 份文档** | 🔴 致命 | 文档与演示(20%) | 仅有一份 architecture_report.md |
| G3 | **无知识图谱** | 🟠 重要 | 功能完整性(30%) | 赛题明确要求"纳入知识图谱"但没有实现 |
| G4 | **多模态检索不完整** | 🟠 重要 | 功能完整性(30%) | 图片检索仅基于文本描述标签，非真正多模态视觉理解 |

### 4.2 重要改进项

| 编号 | 问题 | 类型 | 说明 |
|------|------|------|------|
| G5 | `.env` 含真实 API Key 已提交 | 安全 | 仓库历史需清理，Key 需轮换 |
| G6 | JWT SECRET_KEY 硬编码 | 安全 | `auth_service.py:10` 需改为环境变量 |
| G7 | 密码哈希用 sha256_crypt 非 bcrypt | 安全 | `auth_service.py:8` 声明为 bcrypt 但实际用 SHA256 |
| G8 | CORS 全开 | 安全 | 生产环境需限制域名 |
| G9 | 缺少日志系统 | 稳定性 | 无结构化日志 / 无错误追踪 |
| G10 | 对话存储内存级 | 可靠性 | 重启即丢失，建议持久化 |
| G11 | 无 OpenCV 依赖声明 | 依赖 | `chat.py` 用到 cv2 但 requirements.txt 无 |
| G12 | 无 SpeechRecognition 依赖声明 | 依赖 | `chat.py` 用到但 requirements.txt 无 |
| G13 | 侧边栏管理员视图遮盖普通用户 | UI | `Layout.vue` 中管理员模式下所有普通导航被隐藏 |
| G14 | 部分后端路由缺少异常处理 | 可靠性 | `knowledge.py` 等未处理空结果等边界情况 |

### 4.3 建议优先级（按比赛评分权重）

```
紧急 (初赛前必须完成):
  G1  — LoongArch/Kylin 部署验证 + Dockerfile
  G2  — 补齐 5 份竞赛文档
  
重要 (显著影响评分):
  G3  — 知识图谱整合 (至少 Neo4j 基础关联)
  G4  — 接入真正多模态模型 (如 Qwen-VL / GPT-4V)
  G5  — 清理密钥 + 环境变量安全
  
建议 (提升用户体验分):
  G6-G8 — 安全加固
  G9    — 日志系统
  G13   — Layout 导航修复
```

---

## 五、技术债务清单

| 类别 | 项 | 文件 | 行号 |
|------|----|------|------|
| 🔴 安全 | SECRET_KEY 硬编码 | `backend/services/auth_service.py` | `10` |
| 🔴 安全 | API Key 在代码库中 | `backend/.env` | — |
| 🟡 架构 | ChromaDB 已安装未使用 | 仅 `config.py` 定义路径 | — |
| 🟡 架构 | V1 向量服务仍被引用 | `routers/search.py` 保留 `vector_service` 导入 | `3` |
| 🟡 代码 | `dataxyy.json` 根目录冗余 | 根目录 | — |
| 🟡 依赖 | opencv-python 未声明 | `routers/chat.py` | `165` |
| 🟡 依赖 | SpeechRecognition 未声明 | `routers/chat.py` | `157` |
| 🟢 UI | 管理员视图隐藏导航 | `frontend/src/components/Layout.vue` | `14-27` |

---

## 六、AI / RAG 管道评估

### 6.1 当前架构

```
[用户输入] → Tokenize(中文分词) → TF-IDF 向量化 → 余弦相似度计算 → Top-K 结果
                                              ↓
                                    可选: LLM 生成检修方案
                                              ↓
                                    可选: 章节推荐 (占比≥40%触发)
```

### 6.2 局限性

1. **TF-IDF vs Embedding**: 自研 TF-IDF 无语义理解，`"发动机异响"` 和 `"引擎噪音"` 余弦相似度为 0
2. **非多模态**: 图片检索索引的是图片的文字描述而非视觉特征
3. **无 RAG 管道**: 当前检索 + LLM 生成是两步独立操作，未实现真正 RAG（检索增强生成）

### 6.3 建议改进

1. 用 `text2vec-base-chinese` 或 `bge-m3` 替换 TF-IDF 进行语义向量化
2. 接入多模态视觉模型处理图片
3. 构建 RAG pipeline: `检索 → 上下文拼接 → LLM 回答 → 来源引用`

---

## 七、初赛提交检查清单

| 提交项 | 状态 | 备注 |
|--------|------|------|
| 1. 软件功能需求分析文档 | ❌ | 需要补充 |
| 2. 软件功能设计文档 | ❌ | 需要补充 |
| 3. 软件产品说明书 | ❌ | 需要补充 |
| 4. 软件功能测试报告 | ❌ | 需要补充 |
| 5. 软件安装包及部署文档 | ✅ | 本文档正在生成 |
| 6. 软件源文件 | ✅ | 完整 |
| 7. 软件功能演示PPT文档 | ❌ | 可以从 `2系统图.pptx` 完善 |
| 8. 功能演示视频(≤7分钟) | ❌ | 需录制 |
| LoongArch + 银河麒麟部署验证 | ❌ | **0分条款，必须完成** |

---

## 八、代码覆盖率（已有）

- **后端路由**: 8 模块, ~40+ API 端点
- **前端页面**: 11 视图组件
- **数据模型**: 5 核心模型 (User, Guidance, CommunityPost, Knowledge, Document)
- **服务层**: 8 个 Service 类
- **测试**: 2 个测试脚本 (`test_community.py`, `test_search.py`) — 非单元测试
