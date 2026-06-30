"""
LLM 路由调度器
支持 DeepSeek / Qwen API，hybrid 模式保留任务难度分级
"""
import json
from typing import Optional
from openai import OpenAI
from config.settings import settings


class LLMRouter:
    """LLM 多模型路由调度"""

    def __init__(self):
        self._deepseek_client: Optional[OpenAI] = None
        self._qwen_client: Optional[OpenAI] = None

    @property
    def deepseek(self) -> OpenAI:
        if self._deepseek_client is None:
            self._deepseek_client = OpenAI(
                api_key=settings.DEEPSEEK_API_KEY,
                base_url=settings.DEEPSEEK_API_BASE,
            )
        return self._deepseek_client

    @property
    def qwen(self) -> OpenAI:
        if self._qwen_client is None:
            self._qwen_client = OpenAI(
                api_key=settings.QWEN_API_KEY,
                base_url=settings.QWEN_API_BASE,
            )
        return self._qwen_client

    def chat(self, messages: list, model: Optional[str] = None) -> str:
        """通用对话"""
        client = self.deepseek if settings.DEEPSEEK_API_KEY else self.qwen
        model_name = model or settings.DEEPSEEK_MODEL
        resp = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.7,
        )
        return resp.choices[0].message.content

    def chat_stream(self, messages: list, model: Optional[str] = None):
        """流式对话"""
        client = self.deepseek if settings.DEEPSEEK_API_KEY else self.qwen
        model_name = model or settings.DEEPSEEK_MODEL
        stream = client.chat.completions.create(
            model=model_name,
            messages=messages,
            temperature=0.7,
            stream=True,
        )
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta

    def analyze_image(self, image_url: str, prompt: str = "请描述这张图片中的设备状态和可能的故障") -> str:
        """Qwen2.5-VL 图片理解"""
        resp = self.qwen.chat.completions.create(
            model=settings.QWEN_VL_MODEL,
            messages=[{
                "role": "user",
                "content": [
                    {"type": "image_url", "image_url": {"url": image_url}},
                    {"type": "text", "text": prompt},
                ],
            }],
        )
        return resp.choices[0].message.content

    def classify_difficulty(self, query: str) -> str:
        """任务难度分级 (hybrid 模式用)"""
        score = 0
        high_kw = ["故障", "复杂", "严重", "紧急", "异常", "报错", "无法启动", "卡死", "崩溃", "烧毁", "泄漏", "异响"]
        mid_kw = ["维修", "更换", "安装", "调试", "检查", "清洗", "保养", "校准", "检测", "拆卸"]
        low_kw = ["查询", "查看", "说明", "解释", "什么是", "如何", "步骤", "方法", "指南", "手册"]

        q = query.lower()
        for kw in high_kw:
            if kw in q:
                score += 3
        for kw in mid_kw:
            if kw in q:
                score += 2
        for kw in low_kw:
            if kw in q:
                score += 1
        if len(query) > 100:
            score += 2
        elif len(query) > 50:
            score += 1

        if score >= 6:
            return "high"
        elif score >= 3:
            return "medium"
        return "low"


llm = LLMRouter()
