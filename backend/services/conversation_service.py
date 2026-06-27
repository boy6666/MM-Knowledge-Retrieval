"""
对话服务：支持多轮对话、上下文管理
"""
import uuid
import time
from typing import Optional, List, Dict


class Conversation:
    """单个对话会话"""
    def __init__(self, conversation_id: str = None):
        self.id = conversation_id or str(uuid.uuid4())
        self.messages: List[Dict] = []
        self.created_at = time.time()
        self.last_active = time.time()

    def add_message(self, role: str, content: str, media_type: str = "text", media_url: str = ""):
        """添加消息"""
        self.messages.append({
            "role": role,
            "content": content,
            "media_type": media_type,
            "media_url": media_url,
            "timestamp": time.time()
        })
        self.last_active = time.time()

    def get_context(self, max_messages: int = 10):
        """获取对话上下文（最近N条消息）"""
        return self.messages[-max_messages:]

    def clear(self):
        """清空对话"""
        self.messages = []


class ConversationService:
    """对话管理服务"""
    def __init__(self, max_conversations: int = 100, max_idle_seconds: int = 3600):
        self.conversations: Dict[str, Conversation] = {}
        self.max_conversations = max_conversations
        self.max_idle_seconds = max_idle_seconds

    def create_conversation(self) -> Conversation:
        """创建新对话"""
        self._cleanup_idle()
        if len(self.conversations) >= self.max_conversations:
            self._remove_oldest()

        conv = Conversation()
        self.conversations[conv.id] = conv
        return conv

    def get_conversation(self, conversation_id: str) -> Optional[Conversation]:
        """获取对话"""
        self._cleanup_idle()
        conv = self.conversations.get(conversation_id)
        if conv:
            conv.last_active = time.time()
        return conv

    def delete_conversation(self, conversation_id: str):
        """删除对话"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]

    def _cleanup_idle(self):
        """清理空闲对话"""
        now = time.time()
        to_delete = [
            cid for cid, conv in self.conversations.items()
            if now - conv.last_active > self.max_idle_seconds
        ]
        for cid in to_delete:
            del self.conversations[cid]

    def _remove_oldest(self):
        """删除最早创建的对话"""
        oldest_id = min(
            self.conversations.keys(),
            key=lambda cid: self.conversations[cid].created_at
        )
        del self.conversations[oldest_id]

    def list_conversations(self) -> List[Dict]:
        """列出所有对话"""
        self._cleanup_idle()
        return [
            {
                "id": conv.id,
                "message_count": len(conv.messages),
                "created_at": conv.created_at,
                "last_active": conv.last_active
            }
            for conv in self.conversations.values()
        ]


conversation_service = ConversationService()
