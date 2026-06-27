from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from config import settings
from services.llm_service import LLMService
from services.auth_service import get_db, oauth2_scheme, get_current_user
from models.task import Guidance, CommunityPost
from models.user import User
from services.vector_service_v2 import vector_service_v2

router = APIRouter(tags=["profile"])

class LLMConfigRequest(BaseModel):
    mode: str
    provider: str = ""
    modelName: str = ""
    apiKey: str = ""
    apiBase: str = ""
    localPath: str = ""

class LLMTestRequest(BaseModel):
    provider: str
    modelName: str = ""
    apiKey: str
    apiBase: str

@router.post("/llm-config")
async def set_llm_config(config: LLMConfigRequest):
    try:
        if config.mode not in ["local", "cloud", "hybrid"]:
            raise HTTPException(status_code=400, detail="不支持的运行模式")
        
        if config.provider and config.provider not in ["qwen", "deepseek", "openai"]:
            raise HTTPException(status_code=400, detail="不支持的模型提供商")
        
        api_key_map = {
            "qwen": ("QWEN_API_KEY", "QWEN_API_BASE"),
            "deepseek": ("DEEPSEEK_API_KEY", "DEEPSEEK_API_BASE"),
            "openai": ("OPENAI_API_KEY", "OPENAI_API_BASE")
        }
        
        with open(".env", "w") as f:
            f.write(f"DEBUG=true\n")
            f.write(f"PORT={settings.PORT}\n")
            f.write(f"LLM_MODE={config.mode}\n")
            f.write(f"LLM_PROVIDER={config.provider}\n")
            f.write(f"LLM_MODEL_NAME={config.modelName}\n")
            f.write(f"QWEN_API_KEY=\n")
            f.write(f"QWEN_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1\n")
            f.write(f"DEEPSEEK_API_KEY=\n")
            f.write(f"DEEPSEEK_API_BASE=https://api.deepseek.com/v1\n")
            f.write(f"OPENAI_API_KEY=\n")
            f.write(f"OPENAI_API_BASE=https://api.openai.com/v1\n")
            
            if config.provider and config.apiKey:
                key_name, base_name = api_key_map.get(config.provider, ("", ""))
                if key_name:
                    f.write(f"{key_name}={config.apiKey}\n")
                    if config.apiBase:
                        f.write(f"{base_name}={config.apiBase}\n")
            
            f.write(f"LOCAL_LLM_PATH={config.localPath}\n")
        
        return {"success": True, "message": "配置已保存，重启后端后生效"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.post("/test-llm")
async def test_llm_connection(config: LLMTestRequest):
    try:
        if config.provider not in ["qwen", "deepseek", "openai"]:
            raise HTTPException(status_code=400, detail="不支持的模型提供商")
        
        from langchain_openai import ChatOpenAI
        
        model_name = config.modelName or {
            "qwen": "qwen-plus",
            "deepseek": "deepseek-chat",
            "openai": "gpt-4o-mini"
        }.get(config.provider, "qwen-plus")
        
        test_model = ChatOpenAI(
            model_name=model_name,
            openai_api_key=config.apiKey,
            openai_api_base=config.apiBase,
            temperature=0.7
        )
        
        if not test_model:
            raise HTTPException(status_code=400, detail="模型初始化失败")
        
        from langchain_core.messages import HumanMessage, SystemMessage
        messages = [
            SystemMessage(content="你是一个测试助手"),
            HumanMessage(content="请回复'测试成功'")
        ]
        
        response = test_model.invoke(messages)
        content = response.content if hasattr(response, 'content') else str(response)
        
        if "测试成功" in content:
            return {"success": True, "message": f"大模型连接正常（{model_name}）"}
        else:
            return {"success": True, "message": f"连接成功，响应：{content[:50]}"}
    except Exception as e:
        return {"success": False, "message": str(e)}

@router.get("/info")
async def get_user_info(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        user = get_current_user(db, token)
        if not user:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
        return {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "role": user.role,
                "created_at": user.created_at.isoformat() if user.created_at else None
            }
        }
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/stats")
async def get_user_stats(user_id: int = None, db: Session = Depends(get_db)):
    try:
        guidance_query = db.query(Guidance)
        if user_id:
            guidance_query = guidance_query.filter(Guidance.author_id == user_id)
        
        total_guidance = guidance_query.count()
        
        post_query = db.query(CommunityPost)
        if user_id:
            post_query = post_query.filter(CommunityPost.author_id == user_id)
        
        total_posts = post_query.count()
        
        knowledge_count = len(vector_service_v2.chunks) if vector_service_v2 else 0
        image_count = len(vector_service_v2.images) if vector_service_v2 else 0
        
        return {
            "success": True,
            "data": {
                "my_guidance": total_guidance,
                "my_posts": total_posts,
                "uploaded_docs": 1,
                "total_knowledge": knowledge_count + image_count
            }
        }
    except Exception as e:
        return {"success": False, "message": str(e)}