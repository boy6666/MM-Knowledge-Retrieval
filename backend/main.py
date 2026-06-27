"""
设备检修知识检索与作业系统 - 主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import os

from config import settings
from utils.db import init_db
from routers import auth, search, guidance, knowledge, profile, admin, chat, community


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭钩子"""
    # 启动时初始化
    os.makedirs("./data", exist_ok=True)
    os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
    os.makedirs("./data/uploads", exist_ok=True)
    init_db()
    print("[Main] 数据库初始化完成")
    yield
    # 关闭时清理（可扩展）


app = FastAPI(
    title="设备检修知识检索与作业系统",
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

# 路由注册
app.include_router(auth.router, prefix="/api/auth", tags=["认证"])
app.include_router(search.router, prefix="/api/search", tags=["检索"])
app.include_router(guidance.router, prefix="/api/guidance", tags=["检修方案"])
app.include_router(community.router, prefix="/api/community", tags=["经验社区"])
app.include_router(knowledge.router, prefix="/api/knowledge", tags=["知识管理"])
app.include_router(profile.router, prefix="/api/profile", tags=["个人中心"])
app.include_router(admin.router, prefix="/api/admin", tags=["管理"])
app.include_router(chat.router, prefix="/api/chat", tags=["对话"])

# 静态文件服务（图片）
images_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "images")
os.makedirs(images_dir, exist_ok=True)
app.mount("/api/images", StaticFiles(directory=images_dir), name="images")


@app.get("/")
async def root():
    return {
        "code": 200,
        "message": "ok",
        "data": {"name": "设备检修知识检索与作业系统 API", "version": "1.0.0"}
    }


@app.get("/health")
async def health():
    return {"code": 200, "message": "ok", "data": {"status": "healthy"}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
