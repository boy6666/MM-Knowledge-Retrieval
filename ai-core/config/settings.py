"""
AI Core 配置
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # ===== LLM =====
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
    QWEN_API_BASE = os.getenv("QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    QWEN_VL_MODEL = os.getenv("QWEN_VL_MODEL", "qwen-vl-plus")

    LLM_MODE = os.getenv("LLM_MODE", "cloud")  # cloud / hybrid

    # ===== 向量 =====
    EMBEDDING_MODEL_PATH = os.getenv("EMBEDDING_MODEL_PATH", "./models/bge-base-zh-v1.5")
    EMBEDDING_DIM = 768  # bge-base-zh-v1.5 是 768 维

    # ===== PostgreSQL (AGE + pgvector) =====
    PG_HOST = os.getenv("PG_HOST", "localhost")
    PG_PORT = int(os.getenv("PG_PORT", "5432"))
    PG_DB = os.getenv("PG_DB", "motor_maintenance")
    PG_USER = os.getenv("PG_USER", "postgres")
    PG_PASSWORD = os.getenv("PG_PASSWORD", "postgres")
    PG_GRAPH_NAME = os.getenv("PG_GRAPH_NAME", "motor_knowledge")

    # ===== 视觉 =====
    YOLO_MODEL_PATH = os.getenv("YOLO_MODEL_PATH", "./models/yolov8n.onnx")
    YOLO_CONFIDENCE = float(os.getenv("YOLO_CONFIDENCE", "0.5"))

    # ===== 路径 =====
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.getenv("AI_DATA_DIR", os.path.join(os.path.dirname(BASE_DIR), "data"))


settings = Settings()
