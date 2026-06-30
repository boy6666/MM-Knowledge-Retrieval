"""
对话持久化 — PostgreSQL 存储
"""
import uuid
from datetime import datetime, timezone
import psycopg2
import psycopg2.extras
from config.settings import settings


class ConversationStore:
    """对话持久化存储"""

    def __init__(self):
        self._conn = None

    @property
    def conn(self):
        if self._conn is None:
            self._conn = psycopg2.connect(
                host=settings.PG_HOST,
                port=settings.PG_PORT,
                dbname=settings.PG_DB,
                user=settings.PG_USER,
                password=settings.PG_PASSWORD,
            )
            self._conn.autocommit = True
        return self._conn

    def ensure_table(self):
        """建表"""
        cur = self.conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS conversations (
                id UUID PRIMARY KEY,
                user_id INTEGER,
                title TEXT DEFAULT '新对话',
                created_at TIMESTAMP DEFAULT NOW(),
                updated_at TIMESTAMP DEFAULT NOW()
            );
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id BIGSERIAL PRIMARY KEY,
                conversation_id UUID REFERENCES conversations(id),
                role VARCHAR(10) NOT NULL,
                content TEXT NOT NULL,
                media_type VARCHAR(20) DEFAULT 'text',
                media_url TEXT DEFAULT '',
                cited_chunks TEXT[] DEFAULT '{}',
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_messages_conv
            ON messages(conversation_id, created_at);
        """)
        cur.close()

    def create_conversation(self, user_id: int = 0, title: str = "新对话") -> str:
        """创建新对话"""
        conv_id = str(uuid.uuid4())
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO conversations (id, user_id, title) VALUES (%s, %s, %s)",
            (conv_id, user_id, title),
        )
        cur.close()
        return conv_id

    def add_message(self, conversation_id: str, role: str, content: str,
                    media_type: str = "text", media_url: str = "",
                    cited_chunks: list[str] | None = None):
        """添加消息"""
        cur = self.conn.cursor()
        cur.execute(
            """INSERT INTO messages
               (conversation_id, role, content, media_type, media_url, cited_chunks)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (conversation_id, role, content, media_type, media_url,
             cited_chunks or []),
        )
        cur.execute(
            "UPDATE conversations SET updated_at = %s WHERE id = %s",
            (datetime.now(timezone.utc), conversation_id),
        )
        cur.close()

    def get_messages(self, conversation_id: str, limit: int = 50) -> list[dict]:
        """获取对话历史"""
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            """SELECT role, content, media_type, media_url, cited_chunks, created_at
               FROM messages
               WHERE conversation_id = %s
               ORDER BY created_at ASC
               LIMIT %s""",
            (conversation_id, limit),
        )
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]

    def get_context(self, conversation_id: str, max_messages: int = 10) -> list[dict]:
        """获取最近 N 条消息 (作为 LLM 上下文)"""
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            """SELECT role, content FROM messages
               WHERE conversation_id = %s
               ORDER BY created_at DESC
               LIMIT %s""",
            (conversation_id, max_messages),
        )
        rows = cur.fetchall()
        cur.close()
        return list(reversed([{"role": r["role"], "content": r["content"]} for r in rows]))

    def list_conversations(self, user_id: int = 0, limit: int = 20) -> list[dict]:
        """列出用户对话"""
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            """SELECT id, title, created_at, updated_at
               FROM conversations
               WHERE user_id = %s
               ORDER BY updated_at DESC
               LIMIT %s""",
            (user_id, limit),
        )
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]

    def delete_conversation(self, conversation_id: str):
        """删除对话"""
        cur = self.conn.cursor()
        cur.execute("DELETE FROM messages WHERE conversation_id = %s", (conversation_id,))
        cur.execute("DELETE FROM conversations WHERE id = %s", (conversation_id,))
        cur.close()


store = ConversationStore()
