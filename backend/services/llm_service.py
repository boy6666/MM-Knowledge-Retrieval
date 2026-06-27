from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from config import settings
import re

class LLMService:
    def __init__(self):
        self.mode = settings.LLM_MODE
        self.provider = settings.LLM_PROVIDER
        self.model_name = settings.LLM_MODEL_NAME
        self.cloud_model = None
        self.local_model = None
        
        if (self.mode == "cloud" or self.mode == "hybrid") and self.provider:
            self.cloud_model = self._create_cloud_model()
    
    def _create_cloud_model(self):
        if self.provider == "qwen" and settings.QWEN_API_KEY:
            model_name = self.model_name or "qwen-plus"
            return ChatOpenAI(
                model_name=model_name,
                openai_api_key=settings.QWEN_API_KEY,
                openai_api_base=settings.QWEN_API_BASE,
                temperature=0.7
            )
        elif self.provider == "deepseek" and settings.DEEPSEEK_API_KEY:
            model_name = self.model_name or "deepseek-chat"
            return ChatOpenAI(
                model_name=model_name,
                openai_api_key=settings.DEEPSEEK_API_KEY,
                openai_api_base=settings.DEEPSEEK_API_BASE,
                temperature=0.7
            )
        elif self.provider == "openai" and settings.OPENAI_API_KEY:
            model_name = self.model_name or "gpt-4o-mini"
            return ChatOpenAI(
                model_name=model_name,
                openai_api_key=settings.OPENAI_API_KEY,
                openai_api_base=settings.OPENAI_API_BASE,
                temperature=0.7
            )
        return None
    
    def _classify_task_difficulty(self, query: str) -> str:
        difficulty_keywords = {
            'high': ['故障', '复杂', '严重', '紧急', '异常', '报错', '无法启动', '卡死', '崩溃', '烧毁', '泄漏', '异响'],
            'medium': ['维修', '更换', '安装', '调试', '检查', '清洗', '保养', '校准', '检测', '拆卸'],
            'low': ['查询', '查看', '说明', '解释', '什么是', '如何', '步骤', '方法', '指南', '手册']
        }
        
        query_lower = query.lower()
        score = 0
        
        for keyword in difficulty_keywords['high']:
            if keyword in query_lower:
                score += 3
        
        for keyword in difficulty_keywords['medium']:
            if keyword in query_lower:
                score += 2
        
        for keyword in difficulty_keywords['low']:
            if keyword in query_lower:
                score += 1
        
        query_length = len(query)
        if query_length > 100:
            score += 2
        elif query_length > 50:
            score += 1
        
        tech_terms = ['扭矩', '公差', '间隙', '液压', '电气', '电路', '传感器', '编码器', '伺服', 'PLC']
        for term in tech_terms:
            if term in query_lower:
                score += 1
        
        if score >= 6:
            return 'high'
        elif score >= 3:
            return 'medium'
        else:
            return 'low'
    
    def _select_model(self, query: str):
        if self.mode == "cloud":
            return self.cloud_model, "cloud"
        elif self.mode == "local":
            return self.local_model, "local"
        elif self.mode == "hybrid":
            difficulty = self._classify_task_difficulty(query)
            if difficulty == 'high':
                return self.cloud_model, "cloud"
            else:
                return self.local_model, "local"
        return None, "unknown"
    
    def chat(self, messages: list):
        user_query = ""
        for msg in messages:
            if hasattr(msg, 'content'):
                user_query = msg.content
                break
        
        model, provider = self._select_model(user_query)
        
        if not model:
            if self.mode == "hybrid":
                return {"response": "混合模式下，本地模型不可用且云端模型未配置，请检查配置。", "provider": "hybrid", "difficulty": "unknown"}
            elif self.mode == "cloud":
                return {"response": "云端模型未配置，请检查API密钥和提供商设置。", "provider": "cloud", "difficulty": "unknown"}
            else:
                return {"response": "本地模型尚未配置，请使用云端API模式或混合模式。", "provider": "local", "difficulty": "unknown"}
        
        system_msg = SystemMessage(content="你是一个专业的设备检修专家助手。请根据用户的问题，提供准确、专业的检修建议。")
        all_messages = [system_msg] + messages
        
        try:
            response = model.invoke(all_messages)
            difficulty = self._classify_task_difficulty(user_query) if self.mode == "hybrid" else "unknown"
            return {"response": response.content, "provider": provider, "difficulty": difficulty}
        except Exception as e:
            return {"response": f"服务暂不可用: {str(e)}", "provider": "error", "difficulty": "unknown"}
    
    def analyze_image(self, image_path: str):
        model, provider = self._select_model(image_path)
        
        if not model:
            if self.mode == "hybrid":
                return {"query": "", "description": "混合模式下，本地模型不支持图片分析，云端模型未配置。", "provider": "hybrid"}
            elif self.mode == "cloud":
                return {"query": "", "description": "云端模型未配置，请检查API密钥和提供商设置。", "provider": "cloud"}
            else:
                return {"query": "", "description": "无法分析图片，本地模型不支持图片分析，请切换到云端或混合模式。", "provider": "local"}
        
        try:
            messages = [
                SystemMessage(content="你是一个专业的设备故障诊断专家。请分析这张图片，识别设备类型和可能的故障，并生成一个检索查询词。"),
                HumanMessage(content=f"请分析这张设备图片，描述设备状态、识别可能的故障，并生成一个用于检索检修方案的查询词。图片路径: {image_path}")
            ]
            
            response = model.invoke(messages)
            content = response.content
            
            return {
                "description": content,
                "query": content[:100] if content else "",
                "provider": provider
            }
        except Exception as e:
            return {"query": "", "description": f"图片分析失败: {str(e)}", "provider": "error"}
    
    def generate_guide(self, device_type: str, fault_type: str):
        query = f"{device_type} {fault_type}"
        model, provider = self._select_model(query)
        
        default_steps = [
            {"step": 1, "content": f"确认{device_type}的{fault_type}故障现象，记录故障详情"},
            {"step": 2, "content": "准备检修工具和安全防护设备"},
            {"step": 3, "content": "查阅维修手册，了解相关部件结构"},
            {"step": 4, "content": "拆卸相关部件，检查故障部位"},
            {"step": 5, "content": "测量并记录关键参数，判断故障原因"},
            {"step": 6, "content": "更换或修复损坏部件"},
            {"step": 7, "content": "重新组装，确认各部件安装到位"},
            {"step": 8, "content": "测试运行，验证故障是否排除"},
            {"step": 9, "content": "清理现场，填写检修记录"}
        ]
        
        if not model:
            difficulty = self._classify_task_difficulty(query) if self.mode == "hybrid" else "unknown"
            return {"steps": default_steps, "summary": f"{device_type} {fault_type} 标准检修流程", "provider": provider, "difficulty": difficulty}
        
        try:
            messages = [
                SystemMessage(content="你是一个专业的设备检修流程设计师。请根据设备类型和故障类型，生成标准化的检修步骤。"),
                HumanMessage(content=f"请为设备类型'{device_type}'的故障'{fault_type}'生成标准化检修步骤。步骤要清晰、安全、可操作。")
            ]
            
            response = model.invoke(messages)
            content = response.content
            
            steps = []
            for i, line in enumerate(content.split('\n'), 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    steps.append({"step": i, "content": line})
            
            if not steps:
                steps = default_steps
            
            difficulty = self._classify_task_difficulty(query) if self.mode == "hybrid" else "unknown"
            return {"steps": steps, "summary": content, "provider": provider, "difficulty": difficulty}
        except Exception as e:
            difficulty = self._classify_task_difficulty(query) if self.mode == "hybrid" else "unknown"
            return {"steps": default_steps, "summary": f"{device_type} {fault_type} 标准检修流程（AI生成失败，使用默认模板）", "provider": provider, "difficulty": difficulty}

llm_service = LLMService()