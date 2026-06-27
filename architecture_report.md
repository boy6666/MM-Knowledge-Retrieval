# 设备检修知识检索与作业系统 - 架构设计与技术栈报告

## 1. 系统概述

### 1.1 项目定位

本系统是一个面向设备检修领域的**智能知识检索与作业指导系统**，核心目标是帮助维修人员快速获取设备检修知识、生成标准化检修方案，并支持经验共享与AI辅助诊断。

### 1.2 核心功能模块

| 模块 | 功能描述 |
|------|----------|
| **智能检索** | 支持文本检索、图片检索、混合检索，基于TF-IDF向量匹配 |
| **检修方案** | 自动生成/手动创建检修方案，支持方案管理与分享 |
| **经验社区** | 用户发布维修经验帖，支持审核机制 |
| **AI对话** | 多模态对话能力，支持文字、图片、语音、视频交互 |
| **知识管理** | 维修手册解析、知识库管理 |
| **用户中心** | 用户注册登录、个人信息管理、统计数据 |
| **管理后台** | 用户管理、内容审核、数据统计 |

---

## 2. 技术栈清单

### 2.1 后端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.12 | 后端开发语言 |
| FastAPI | 0.110.0 | Web框架，高性能异步API |
| Uvicorn | 0.29.0 | ASGI服务器 |
| SQLAlchemy | 2.0.27 | ORM框架，数据库操作 |
| SQLite | 内置 | 轻量级数据库 |
| LangChain | 0.1.10 | LLM应用开发框架 |
| LangChain-OpenAI | 0.1.0 | OpenAI兼容接口 |
| ChromaDB | 0.4.24 | 向量数据库（备选） |
| PyPDF | 4.2.0 | PDF文档解析 |
| python-jose | 3.3.0 | JWT令牌生成与验证 |
| passlib | 1.7.4 | 密码哈希（bcrypt） |
| python-multipart | 0.0.9 | 文件上传处理 |

### 2.2 前端技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| Vue | 3.4.21 | 前端框架 |
| Vue Router | 4.3.0 | 路由管理 |
| Pinia | 2.1.7 | 状态管理 |
| Element Plus | 2.5.6 | UI组件库 |
| Axios | 1.6.7 | HTTP客户端 |
| TypeScript | 5.4.2 | 类型安全 |
| Vite | 5.2.0 | 构建工具 |

### 2.3 AI能力

| 能力 | 实现方式 | 说明 |
|------|----------|------|
| LLM多模型调度 | LangChain + 多提供商 | 支持Qwen/DeepSeek/OpenAI |
| 向量检索 | 自研TF-IDF引擎 | 基于余弦相似度 |
| RAG管道 | 检索→增强→生成 | 检索增强生成流程 |
| 多模态交互 | LLM + 语音/视频处理 | 支持文字、图片、语音、视频 |
| 任务难度分级 | 关键词匹配算法 | 自动分类任务难度 |

---

## 3. 分层架构设计

### 3.1 架构视图

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端层 (Frontend)                        │
│  Vue 3 + TypeScript + Element Plus + Vue Router + Pinia         │
│  ┌─────────┬─────────┬─────────┬─────────┬─────────┐           │
│  │  Home   │ Search  │Guidance │Community│ Profile │  ...      │
│  └────┬────┴────┬────┴────┬────┴────┬────┴────┬────┘           │
└───────┼─────────┼─────────┼─────────┼─────────┼─────────────────┘
        │         │         │         │         │
        ▼         ▼         ▼         ▼         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        API网关层 (API Gateway)                   │
│                    FastAPI + CORS + Static Files                 │
│  /api/auth    /api/search    /api/guidance    /api/community    │
│  /api/profile /api/knowledge /api/chat       /api/admin         │
└───────┬─────────┬─────────┬─────────┬─────────┬─────────────────┘
        │         │         │         │         │
        ▼         ▼         ▼         ▼         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        业务逻辑层 (Service Layer)                │
│  ┌────────────┬────────────┬────────────┬────────────┐           │
│  │ AuthService│SearchService│GuidanceService│CommunityService│   │
│  ├────────────┼────────────┼────────────┼────────────┤           │
│  │LLMService  │VectorService│DataProcessor│ChatService │           │
│  └────────────┴────────────┴────────────┴────────────┘           │
└───────┬─────────┬─────────┬─────────┬─────────┬─────────────────┘
        │         │         │         │         │
        ▼         ▼         ▼         ▼         ▼
┌─────────────────────────────────────────────────────────────────┐
│                        数据层 (Data Layer)                       │
│  ┌───────────────┐  ┌───────────────┐  ┌───────────────┐       │
│  │   SQLite DB   │  │  TF-IDF Index │  │   ChromaDB    │       │
│  │ (app.db)      │  │  (JSON文件)   │  │ (向量数据库)   │       │
│  └───────────────┘  └───────────────┘  └───────────────┘       │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 核心组件职责

#### 3.2.1 路由层 (Routers)

| 路由文件 | 路径前缀 | 职责 |
|----------|----------|------|
| `auth.py` | `/api/auth` | 用户注册、登录、Token获取 |
| `search.py` | `/api/search` | 文本检索、图片检索、混合检索、智能推荐 |
| `guidance.py` | `/api/guidance` | 检修方案生成、保存、查询、删除 |
| `community.py` | `/api/community` | 社区帖子CRUD、点赞、审核 |
| `knowledge.py` | `/api/knowledge` | 知识库管理、文档上传 |
| `profile.py` | `/api/profile` | 用户信息、统计数据、LLM配置 |
| `chat.py` | `/api/chat` | AI对话、语音转文字、视频分析、图片生成 |
| `admin.py` | `/api/admin` | 用户管理、内容审核、数据统计 |

#### 3.2.2 服务层 (Services)

| 服务文件 | 职责 |
|----------|------|
| `auth_service.py` | 用户认证、Token生成、密码哈希 |
| `guidance_service.py` | 检修方案业务逻辑、权限控制 |
| `community_service.py` | 社区帖子业务逻辑、审核流程 |
| `conversation_service.py` | 对话管理、消息存储 |
| `llm_service.py` | LLM调用、模型调度、任务难度分级 |
| `vector_service_v2.py` | 自研TF-IDF向量检索引擎 |
| `data_processor_v2.py` | PDF版面解析、章节分块、图文绑定 |

#### 3.2.3 数据层 (Models)

| 模型文件 | 表名 | 核心字段 |
|----------|------|----------|
| `user.py` | `users` | id, username, password_hash, email, role |
| `task.py` | `guidance` | id, title, content, author_id, is_public |
| `task.py` | `community_posts` | id, title, content, author_id, status |
| `knowledge.py` | `knowledge` | id, title, content, category, device_type |
| `knowledge.py` | `documents` | id, filename, filepath, uploaded_by |

---

## 4. 数据模型设计

### 4.1 用户模型 (User)

```
+------------------+
|      users       |
+------------------+
| id (PK, int)     |
| username (str)   |  ← 唯一索引
| password_hash    |
| email (str)      |  ← 唯一索引
| role (str)       |  ← 默认"user"，可选"admin"
| created_at       |  ← datetime
| updated_at       |  ← datetime
+------------------+
```

### 4.2 检修方案模型 (Guidance)

```
+------------------+
|    guidance      |
+------------------+
| id (PK, int)     |
| title (str)      |  ← 必填
| device_type      |  ← 设备类型
| fault_type       |  ← 故障类型
| content (text)   |  ← 方案内容
| source_type      |  ← "llm_generated"或"manual"
| source_id        |  ← 来源ID
| author_id        |  ← 作者ID（可为空，匿名）
| is_public        |  ← 是否公开
| status           |  ← "draft"或"published"
| views            |  ← 浏览次数
| likes            |  ← 点赞数
| created_at       |
| updated_at       |
+------------------+
```

### 4.3 社区帖子模型 (CommunityPost)

```
+---------------------+
|  community_posts    |
+---------------------+
| id (PK, int)        |
| title (str)         |  ← 必填
| device_type         |
| fault_type          |
| content (text)      |
| images (text)       |  ← JSON数组
| author_id           |
| author_name         |  ← 默认"匿名用户"
| status              |  ← "pending"待审核/"approved"已通过
| likes               |
| views               |
| created_at          |
| reviewed_at         |
| reviewer_id         |
| review_comment      |
+---------------------+
```

### 4.4 知识文档模型 (Knowledge/Document)

```
+-------------+     +-------------+
|  knowledge  |     |  documents  |
+-------------+     +-------------+
| id (PK)     |     | id (PK)     |
| title       |     | filename    |
| content     |     | filepath    |
| category    |     | file_type   |
| source      |     | size        |
| device_type |     | knowledge_id| ← FK
| status      |     | uploaded_by |
| creator_id  |     | uploaded_at |
| created_at  |     +-------------+
| updated_at  |
+-------------+
```

---

## 5. AI/RAG管道流程

### 5.1 智能检索流程

```
用户查询 → 分词(tokenize) → TF-IDF向量化 → 余弦相似度计算 → 返回Top-K结果
                                                          ↓
                                               智能章节推荐判断
                                               (占比≥40%触发)
                                                          ↓
                                               返回章节建议
```

### 5.2 检修方案生成流程

```
用户请求 → 获取相关知识(检索) → LLM生成方案 → 保存到数据库 → 返回方案ID
              ↓                    ↓
         向量检索引擎          LLM多模型调度
```

### 5.3 LLM模型调度策略

| 模式 | 策略 |
|------|------|
| **local** | 始终使用本地模型 |
| **cloud** | 始终使用云端模型 |
| **hybrid** | 根据任务难度自动选择：高难度用云端，低难度用本地 |

**任务难度分级算法：**
- 高难度关键词：故障、复杂、严重、紧急、异常、报错、无法启动、卡死、崩溃、烧毁、泄漏、异响
- 中难度关键词：维修、更换、安装、调试、检查、清洗、保养、校准、检测、拆卸
- 低难度关键词：查询、查看、说明、解释、什么是、如何、步骤、方法、指南、手册

### 5.4 PDF数据处理流程

```
PDF文件 → 版面解析(TextBlock/ImageBlock) → 章节树构建 → 图文关联 → 分块存储
                                                      ↓
                                                AI图像分析(可选)
```

---

## 6. 安全机制

### 6.1 认证与授权

| 机制 | 实现方式 |
|------|----------|
| 用户认证 | JWT Token + OAuth2 Password Flow |
| 密码安全 | bcrypt哈希存储 |
| 权限控制 | 基于角色(role字段)：user/admin |
| 方案删除权限 | 已登录用户只能删除自己创建的方案；未登录用户只能删除匿名方案 |

### 6.2 API安全

| 措施 | 说明 |
|------|------|
| CORS配置 | 允许所有来源(开发环境) |
| 静态文件服务 | 限制在指定目录 |
| 输入验证 | FastAPI Pydantic模型验证 |
| 异常处理 | HTTPException统一处理 |

---

## 7. 部署拓扑

### 7.1 开发环境

```
┌──────────────┐     ┌──────────────┐
│  Frontend    │     │   Backend    │
│  Vite Dev    │────▶│  Uvicorn     │
│  localhost   │     │  localhost   │
│  :5173       │     │  :8000       │
└──────────────┘     └──────┬───────┘
                            │
                            ▼
                   ┌──────────────┐
                   │   SQLite     │
                   │   app.db     │
                   └──────────────┘
```

### 7.2 配置管理

环境变量配置文件：`.env`

| 配置项 | 说明 | 默认值 |
|--------|------|--------|
| `DEBUG` | 调试模式 | `false` |
| `PORT` | 服务端口 | `8000` |
| `LLM_MODE` | LLM模式 | `local` |
| `LLM_PROVIDER` | LLM提供商 | 空 |
| `QWEN_API_KEY` | 通义千问API密钥 | 空 |
| `DEEPSEEK_API_KEY` | DeepSeek API密钥 | 空 |
| `OPENAI_API_KEY` | OpenAI API密钥 | 空 |
| `LOCAL_LLM_PATH` | 本地模型路径 | `./models/qwen-7b-int4.gguf` |

---

## 8. API接口清单

### 8.1 认证接口 (/api/auth)

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/register` | 用户注册 |
| POST | `/token` | 获取登录Token |

### 8.2 检索接口 (/api/search)

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/text` | 文本检索 |
| POST | `/image` | 图片检索 |
| POST | `/hybrid` | 混合检索 |
| GET | `/suggest` | 智能章节推荐 |

### 8.3 检修方案接口 (/api/guidance)

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/generate` | 生成检修方案 |
| POST | `/save` | 保存检修方案 |
| GET | `/{guidance_id}` | 获取方案详情 |
| GET | `/list/mine` | 获取我的方案 |
| GET | `/list/public` | 获取公开方案 |
| DELETE | `/{guidance_id}` | 删除方案 |
| POST | `/{guidance_id}/public` | 切换公开状态 |

### 8.4 社区接口 (/api/community)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/list` | 获取帖子列表 |
| GET | `/{post_id}` | 获取帖子详情 |
| POST | `/create` | 创建帖子 |
| GET | `/list/mine` | 获取我的帖子 |
| POST | `/{post_id}/like` | 点赞 |
| DELETE | `/{post_id}` | 删除帖子 |
| GET | `/admin/pending` | 获取待审核列表 |
| POST | `/admin/{post_id}/approve` | 审核通过 |
| POST | `/admin/{post_id}/reject` | 审核拒绝 |

### 8.5 对话接口 (/api/chat)

| 方法 | 路径 | 描述 |
|------|------|------|
| POST | `/new` | 创建新对话 |
| GET | `/{conversation_id}` | 获取对话历史 |
| POST | `/{conversation_id}/chat` | 发送消息 |
| DELETE | `/{conversation_id}` | 删除对话 |
| POST | `/speech-to-text` | 语音转文字 |
| POST | `/video-analyze` | 视频分析 |
| POST | `/image-generate` | 图片生成 |

### 8.6 个人中心接口 (/api/profile)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/info` | 获取用户信息 |
| GET | `/stats` | 获取统计数据 |
| POST | `/llm-config` | 设置LLM配置 |
| POST | `/test-llm` | 测试LLM配置 |

### 8.7 管理接口 (/api/admin)

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/users` | 获取用户列表 |
| POST | `/users/{user_id}/role` | 更新用户角色 |
| DELETE | `/users/{user_id}` | 删除用户 |
| GET | `/stats` | 获取统计数据 |
| POST | `/knowledge/{id}/reject` | 拒绝知识审核 |
| DELETE | `/knowledge/{id}` | 删除知识 |

---

## 9. 前端路由设计

| 路径 | 组件 | 需要认证 | 需要管理员 |
|------|------|----------|------------|
| `/` | Home | 否 | 否 |
| `/search` | Search | 否 | 否 |
| `/guidance` | Guidance | 否 | 否 |
| `/guidance/:taskId` | Guidance | 否 | 否 |
| `/community` | Community | 否 | 否 |
| `/community/:postId` | Community | 否 | 否 |
| `/knowledge` | Knowledge | 否 | 否 |
| `/knowledge/:id` | KnowledgeDetail | 否 | 否 |
| `/chat` | Chat | 否 | 否 |
| `/profile` | Profile | 是 | 否 |
| `/login` | Login | 否 | 否 |
| `/register` | Register | 否 | 否 |
| `/admin` | Admin | 是 | 是 |

---

## 10. 已知架构债务与改进建议

### 10.1 已修复问题

| 问题 | 修复方案 | 涉及文件 |
|------|----------|----------|
| 路由双重前缀 | 移除路由文件内部`/api`前缀，统一由`main.py`管理 | `admin.py`, `profile.py`, `main.py` |
| 方案删除权限验证 | 添加`get_optional_current_user`依赖，从JWT获取用户 | `guidance.py`, `guidance_service.py` |
| Vue Router参数名不匹配 | 将`route.params.id`改为`route.params.taskId` | `Guidance.vue` |
| Search.vue跳转路径错误 | 将`/ai`改为`/chat` | `Search.vue` |
| Community.vue未处理路由参数 | 添加读取`route.params.postId`逻辑 | `Community.vue` |

### 10.2 待改进项

| 优先级 | 改进项 | 描述 |
|--------|--------|------|
| **高** | CORS安全限制 | 当前允许所有来源，生产环境应限制具体域名 |
| **高** | 数据库连接池 | 当前无连接池配置，高并发场景需优化 |
| **中** | 向量数据库迁移 | 自研TF-IDF引擎性能有限，建议迁移至专业向量数据库 |
| **中** | 缓存机制 | 添加Redis缓存热门检索结果和方案 |
| **中** | 日志系统 | 添加结构化日志和错误追踪 |
| **低** | API文档完善 | 使用Swagger UI完善接口文档 |

---

## 11. 统计数据

- **后端路由数**：8个模块，40+接口
- **前端页面数**：11个视图组件
- **数据模型数**：5个核心模型
- **数据文件**：支持`dataxyy.json`、`structured_data_v2.json`、`manual_data.json`、`processed_chunks.json`多版本数据
- **图片资源**：58张维修手册插图（`data/data1/images/`）

---

*报告生成时间：2026年6月26日*