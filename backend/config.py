import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
os.makedirs(DATA_DIR, exist_ok=True)

class Settings:
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    PORT = int(os.getenv("PORT", 8000))
    
    DATABASE_URL = f"sqlite:///{os.path.join(DATA_DIR, 'app.db')}"
    CHROMA_DB_PATH = os.path.join(DATA_DIR, "chroma_db")
    
    LLM_MODE = os.getenv("LLM_MODE", "local")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "")
    LLM_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "")
    
    QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
    QWEN_API_BASE = os.getenv("QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
    OPENAI_API_BASE = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    
    LOCAL_LLM_PATH = os.getenv("LOCAL_LLM_PATH", "./models/qwen-7b-int4.gguf")
    
    # JWT 配置（优先级：环境变量 > 此处默认值）
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "")
    JWT_ALGORITHM = "HS256"
    JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "30"))

settings = Settings()