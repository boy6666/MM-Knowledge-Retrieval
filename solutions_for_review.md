# 问题修复方案书

你逐条回复字母即可（如 A-1A, B-2A, C-3A...）

---

## 问题 A：PythonClient 指向旧后端而非 ai-core

**现状：** application.yml 里 `python.base-url: http://localhost:8000`，PythonClient 所有请求发给了旧的 FastAPI。ai-core (:8001) 写好了但根本没人调，路径也对不上。

**解决方式：** 改 PythonClient 的 base-url 和请求路径，同时在 ai-core 上补上缺失的接口。

**具体改动：**

| 文件 | 改什么 |
|------|--------|
| `application.yml` | `base-url: http://localhost:8000` → `http://localhost:8001` |
| `PythonClient.java` | 所有路径加上 `/api/v1/` 前缀 |
| `ai-core/main.py` | 补充 PythonClient 调用的接口 |

**接口映射表：**

| PythonClient 方法 | 当前路径 (:8000) | 新路径 (:8001) | ai-core 状态 |
|------------------|----------------|---------------|-------------|
| `searchText()` | `/api/search/text` | `/api/v1/retrieve` | ✅ 已有 |
| `searchImages()` | `/api/search/images-only` | `/api/v1/retrieve`（加参数区分） | ❌ 需加 |
| `hybridSearch()` | `/api/search/hybrid` | `/api/v1/retrieve` | ✅ 已有 |
| `imageSearch()` | `/api/search/image` | `/api/v1/vision/analyze` | ✅ 已有 |
| `generateGuidance()` | `/api/guidance/generate` | `/api/v1/guidance/workflow` | ✅ 已有（格式需微调） |
| `generateFromChat()` | `/api/guidance/generate-from-chat` | `/api/v1/guidance/generate-from-chat` | ❌ 需新增 |
| `uploadPdf()` | `/api/knowledge/upload` | `/api/v1/knowledge/upload` | ❌ 需新增 |
| `speechToText()` | `/api/chat/speech-to-text` | `/api/v1/speech/stt` | ✅ 已有 |
| `getChapterTree()` | `/api/search/chapter-tree` | ❌ 新架构无章节树 | 建议删除 |
| `getCategories()` | `/api/search/categories` | ❌ 新架构无分类 | 建议删除 |
| `getSearchStats()` | `/api/search/stats` | 可通过 `/health` 查看 | 建议改调用 |
| `testLlm()` | `/api/profile/test-llm` | 用 `/api/v1/chat` 替代 | 建议改逻辑 |
| `setLlmConfig()` | `/api/profile/llm-config` | 环境变量管理，无接口 | 建议删除 |
| `getKbChunks()` | `/api/knowledge/{id}/chunks` | ❌ 新架构改用 pgvector | 建议重写 |

**你的选项：**

| 选项 | 内容 |
|------|------|
| **A-1A** | 按上表全面改 PythonClient + 补 ai-core 缺失接口，删旧后端依赖 |
| **A-1B** | 先不动，等旧后端完全退役时再一次性迁移 |
| **A-1C** | 只改 base-url 和基本路径，别的以后再说 |
| **A-1D** | 你的想法：_________________ |

---

## 问题 B：SecurityConfig 拦截了未登录用户的公开 API

**现状：** 当前只有 `/api/auth/**` 和 `/health` 允许未登录访问，其他所有 API 都需要登录。但赛题要求"未登录可使用基础检索"。

**被拦截的公开 API（应该放开）：**

| API | 用途 |
|-----|------|
| `GET /api/community/list` | 任何人都能看帖子列表 |
| `GET /api/guidance/list/public` | 任何人都能看公开方案 |
| `GET /api/knowledge/list` | 任何人都能看知识库 |
| `GET /api/search/**` | 任何人都能搜索 |
| `GET /api/guidance/{id}` | 任何人都能看单个方案 |
| `GET /api/knowledge/{id}` | 任何人都能看单个知识条目 |

**解决方式：** 在 `SecurityConfig.java` 的 `.permitAll()` 列表追加以上路径。

**你的选项：**

| 选项 | 内容 |
|------|------|
| **B-2A** | 开放全部上述公开 API（社区列表+方案浏览+知识库+搜索，赛题友好） |
| **B-2B** | 只开放搜索，其他要登录 |
| **B-2C** | 全部要登录（最简单，但不符合赛题"未登录可用基础功能"要求） |

---

## 问题 C：Java 后端用 SQLite，ai-core 用 PostgreSQL，数据不互通

**现状：** Java 的 `repair_java.db`（SQLite）存用户/方案/帖子/知识，ai-core 的 `motor_maintenance`（PG）存知识图谱/向量/对话。没有任何机制保证两边数据一致。

**解决方式：** Java 后端改连 PostgreSQL，跟 ai-core 用同一个数据库。

**改动量：**

```yaml
# application.yml 改这一块
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/motor_maintenance
    username: postgres
    password: 1234
  jpa:
    database-platform: org.hibernate.dialect.PostgreSQLDialect
```
- 删掉 `SQLiteDialect.java`（不需要了）
- 删掉 `repair_java.db`（数据需要迁移）

**注意：** JAVA_HOME 显示是 1.8，PostgreSQL JDBC 驱动需要 Java 8+，所以兼容。但如果你选 4B（升 JDK 17）会更稳妥。

**你的选项：**

| 选项 | 内容 |
|------|------|
| **C-3A** | 现在迁 PostgreSQL，跟 ai-core 统一数据库（一次到位） |
| **C-3B** | 保持 SQLite，等 ai-core PG 稳定了再一起迁（分两步走） |
| **C-3C** | 一直用 SQLite（最简单，但知识图谱方案无法落地——AGE+pgvector 需要 PG） |

---

## 问题 D：Java 版本 1.8

**现状：** `pom.xml` 设 `<java.version>1.8`，你本地装的是 OpenJDK 1.8.0_472。Spring Boot 2.7.18 官方支持 Java 8，所以**能跑，不是硬伤**。但长期(Spring Boot 3.x)需要 Java 17。

**你的选项：**

| 选项 | 内容 |
|------|------|
| **D-4A** | 保持 Java 8，能跑就行，不改 |
| **D-4B** | 装 JDK 17，升上去（为以后 Spring Boot 3 做准备） |

---

## 问题 E：前端 vite 代理混乱

**现状：** 前端请求一部分走旧后端 :8000，一部分走 Java :8080：

```typescript
/api/chat              → :8000   // 旧后端
/api/search            → :8000   // 旧后端
/api/knowledge/upload  → :8000   // 旧后端
/api/*                 → :8080   // Java
```

**解决方式：** 删掉指向旧后端的 3 个代理，全部走 Java 8080：

```typescript
server: {
  proxy: {
    '/api': {
      target: 'http://localhost:8080',
      changeOrigin: true
    }
  }
}
```

前提：Java 8080 能提供搜索和对话接口（PythonClient 正确指向 ai-core 之后）。

**你的选项：**

| 选项 | 内容 |
|------|------|
| **E-5A** | 等 A 方案（PythonClient 改连 ai-core）搞定后，统一改成全部走 Java :8080 |
| **E-5B** | 保留现状，后面再改 |

---

## 问题 F：PythonClient 里的老旧接口

**现状：** `PythonClient.java` 里有 3 个方法在新架构中找不到对应接口：

| 方法 | 旧功能 | 新架构替代 |
|------|--------|-----------|
| `getChapterTree()` | 返回 PDF 章节树 | 新架构无此概念，建议删除 |
| `getCategories()` | 返回知识分类 | Java JPA 直接查数据库即可，不用调 Python |
| `setLlmConfig()` | 动态改 LLM 配置 | 新架构用环境变量管理，无运行时接口 |

**你的选项：**

| 选项 | 内容 |
|------|------|
| **F-6A** | 直接删掉这三个方法和对应的 Controller 调用 |
| **F-6B** | 保留（编译能过，但运行时调到就 404） |

---

## 小问题（无需决策，我直接修）

| # | 问题 | 修复方式 |
|---|------|---------|
| 9 | CommunityService 自己写了一套模糊匹配，同时 JPA 也有 LIKE 查询 | 删掉 `matchesFaultType()` 方法，统一用 JPA 的 `LIKE %:keyword%` |
| 10 | 方案生成失败不提示用户 | `generate()` 方法加 try-catch，失败后抛异常 |
| 11 | 前端对话走旧后端 | 依赖 A 方案 + E 方案完成 |
| 12 | .env 有真实 API Key | 已有 `.gitignore`，确认 `.env` 在其中即可 |

---

## 回执格式

直接按这个格式回我，没提到的我默认选建议项：

```
A-1A, B-2A, C-3A, D-4A, E-5A, F-6A
```
