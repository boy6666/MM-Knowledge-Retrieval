"""
AI Core 微服务入口
"""
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from config.settings import settings

# 延迟导入各模块（避免启动时因缺少依赖报错）
llm = None
retriever = None
age = None
yolo = None
stt = None
store = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动/关闭钩子"""
    global llm, retriever, age, yolo, stt, store
    print("[AICore] 启动中...")

    # LLM
    from llm.router import llm as _llm
    llm = _llm

    # 对话存储 (PostgreSQL)
    from conversation.pg_store import store as _store
    store = _store
    try:
        store.ensure_table()
        print("[AICore] 对话表已就绪")
    except Exception as e:
        print(f"[AICore] PostgreSQL 未就绪 (对话持久化不可用): {e}")

    # 知识图谱 (AGE)
    from knowledge_graph.age_client import age as _age
    age = _age
    try:
        age.ensure_graph()
        print(f"[AICore] AGE 图 '{settings.PG_GRAPH_NAME}' 已就绪")
    except Exception as e:
        print(f"[AICore] AGE 未就绪 (图谱查询不可用): {e}")

    # 向量引擎 (pgvector)
    from vector.retriever import retriever as _retriever
    retriever = _retriever
    try:
        retriever.ensure_extension()
        print("[AICore] pgvector 已就绪")
    except Exception as e:
        print(f"[AICore] pgvector 未就绪: {e}")

    # BGE Embedder (print 信息, 实际首次调用时懒加载)
    print(f"[AICore] BGE Embedder 模型: {settings.EMBEDDING_MODEL_PATH}")

    print("[AICore] 启动完成")
    yield
    print("[AICore] 已关闭")


app = FastAPI(
    title="AI Core - 设备检修智能服务",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===== 健康检查 =====
@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "components": {
            "llm": llm is not None,
            "vector": retriever is not None,
            "age": age is not None,
        },
    }


# ===== 检索 =====
@app.post("/api/v1/retrieve")
async def retrieve(query: str, top_k: int = 10, device_type: str = "", include_images: bool = True):
    if not query:
        return {"query": "", "results": [], "total": 0}

    # 1. BGE 向量化
    from vector.embedder import embedder
    query_vec = embedder.encode(query).tolist()

    # 2. pgvector 检索
    results = []
    if retriever:
        try:
            vec_results = retriever.search("embeddings", query_vec, top_k)
            for r in vec_results:
                results.append({
                    "chunk_id": r["chunk_id"],
                    "content": r["content"],
                    "similarity": r["similarity"],
                    "metadata": r.get("metadata", {}),
                })
        except Exception as e:
            print(f"[Retrieve] pgvector 检索失败: {e}")

    # 3. AGE 图谱补充 (如果检索结果不足)
    if len(results) < 3 and age:
        try:
            age_results = age.get_part_info(query)
            for r in age_results:
                results.append({
                    "chunk_id": f"age_{r.get('步骤名称', '')}",
                    "content": r.get("操作说明", ""),
                    "similarity": 0.5,
                    "metadata": r,
                })
        except Exception:
            pass

    return {"query": query, "results": results[:top_k], "total": len(results)}


# ===== 对话 =====
@app.post("/api/v1/chat")
async def chat(
    message: str = Form(...),
    conversation_id: str = Form(""),
    user_id: int = Form(0),
    media_type: str = Form("text"),
    media_url: str = Form(""),
    stream: bool = Form(False),
):
    return await _handle_chat(message, conversation_id, user_id, media_type, media_url, stream)


@app.post("/api/v1/chat-json")
async def chat_json(data: dict):
    return await _handle_chat(
        message=data.get("message", ""),
        conversation_id=data.get("conversation_id", ""),
        user_id=data.get("user_id", 0),
        media_type=data.get("media_type", "text"),
        media_url=data.get("media_url", ""),
        stream=data.get("stream", False),
    )


async def _handle_chat(
    message: str = "",
    conversation_id: str = "",
    user_id: int = 0,
    media_type: str = "text",
    media_url: str = "",
    stream: bool = False,
):
    from llm.router import llm as llm_router

    # 创建/获取对话 (PG 不可用则降级为无持久化)
    conv_id = conversation_id
    if not conv_id:
        import uuid
        conv_id = str(uuid.uuid4())

    # 多模态消息拼接
    full_message = message
    if media_url and media_type == "image":
        try:
            analysis = llm_router.analyze_image(media_url)
            full_message = f"{message}\n[图片分析]: {analysis}"
        except Exception:
            full_message = f"{message}\n[图片上传]"

    # 存储 (try/except 包裹, PG 不可用时静默跳过)
    try:
        if store and conversation_id:
            store.add_message(conversation_id, "user", full_message, media_type, media_url)
    except Exception:
        pass

    # 构建 messages (无上下文, 单轮对话)
    messages = [
        {"role": "system", "content": "你是一个专业的设备检修专家助手。"},
        {"role": "user", "content": full_message},
    ]

    # LLM 调用
    response = llm_router.chat(messages)

    # 存储 AI 回复
    try:
        if store and conversation_id:
            store.add_message(conversation_id, "assistant", response)
    except Exception:
        pass

    return {
        "conversation_id": conv_id,
        "response": response,
        "provider": settings.LLM_MODE,
        "difficulty": llm_router.classify_difficulty(message),
    }


# ===== 标准化作业指引 =====
@app.post("/api/v1/guidance/workflow")
async def get_workflow(data: dict):
    part_name = data.get("part_name", data.get("device_type", ""))
    if not part_name:
        return {"part_name": "", "workflow": [], "total_steps": 0, "error": "缺少 part_name 或 device_type"}
    if not age:
        return {"part_name": part_name, "workflow": [], "message": "AGE 未就绪"}
    try:
        steps = age.get_workflow(part_name)
        return {"part_name": part_name, "workflow": steps, "total_steps": len(steps)}
    except Exception as e:
        return {"part_name": part_name, "workflow": [], "error": str(e)}


# ===== 图片分析 =====
@app.post("/api/v1/vision/analyze")
async def analyze_image(image: UploadFile = File(...), prompt: str = ""):
    # 保存图片
    import os
    save_dir = os.path.join(settings.DATA_DIR, "images")
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, image.filename)
    with open(file_path, "wb") as f:
        f.write(await image.read())

    analysis_text = ""
    detected_parts = []

    # Qwen2.5-VL 分析
    if llm:
        try:
            file_url = f"/images/{image.filename}"
            analysis_text = llm.analyze_image(file_url, prompt or "请描述这张图片中的设备状态和可能的故障")
        except Exception as e:
            analysis_text = f"分析失败: {e}"

    # YOLO 零件检测
    try:
        from vision.yolo_detector import yolo
        detections = yolo.detect_from_path(file_path)
        detected_parts = detections
    except Exception:
        pass

    return {
        "description": analysis_text,
        "detected_parts": detected_parts,
    }


# ===== 案例挂载 =====
@app.post("/api/v1/cases/upload")
async def upload_case(data: dict):
    from knowledge_graph.case_attacher import attacher
    try:
        result = attacher.attach(data)
        return result
    except Exception as e:
        return {"status": "error", "message": str(e)}


# ===== 从对话生成方案 /api/v1/guidance/generate-from-chat =====
@app.post("/api/v1/guidance/generate-from-chat")
async def generate_from_chat(data: dict):
    message_id = data.get("message_id")
    conversation_id = data.get("conversation_id")
    return {
        "guidance_id": None,
        "title": "AI对话方案",
        "content": "请先发起对话，AI将根据对话内容生成检修方案。",
        "device_type": "",
        "fault_type": "",
    }


# ===== 知识上传 /api/v1/knowledge/upload =====
@app.post("/api/v1/knowledge/upload")
async def knowledge_upload(data: dict):
    return {
        "document_id": None,
        "knowledge_id": None,
        "indexed_chunks": 0,
        "message": "知识上传功能依赖 PostgreSQL + pgvector，请先连接数据库。"
    }


# ===== 健康检查 (兼容旧路径) =====
@app.get("/api/health")
async def api_health():
    return await health()


# ===== 主入口 =====
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
