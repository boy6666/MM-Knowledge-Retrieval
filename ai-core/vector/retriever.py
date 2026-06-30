"""
pgvector 检索引擎
PostgreSQL + pgvector 向量存储与检索
"""
from typing import Any
import numpy as np
import psycopg2
import psycopg2.extras
from config.settings import settings


class PgVectorRetriever:
    """pgvector 向量检索引擎"""

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

    def ensure_extension(self):
        """确保 pgvector 扩展已启用"""
        cur = self.conn.cursor()
        cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        cur.close()

    def ensure_table(self, table_name: str = "embeddings"):
        """创建向量表"""
        dim = settings.EMBEDDING_DIM
        cur = self.conn.cursor()
        cur.execute(f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id BIGSERIAL PRIMARY KEY,
                chunk_id TEXT UNIQUE,
                content TEXT NOT NULL,
                metadata JSONB DEFAULT '{{}}',
                embedding vector({dim})
            );
        """)
        cur.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_{table_name}_embedding
            ON {table_name} USING ivfflat (embedding vector_cosine_ops)
            WITH (lists = 100);
        """)
        cur.close()

    def insert(self, table_name: str, chunk_id: str, content: str, embedding: list[float], metadata: dict | None = None):
        """插入向量"""
        cur = self.conn.cursor()
        cur.execute(
            f"""
            INSERT INTO {table_name} (chunk_id, content, embedding, metadata)
            VALUES (%s, %s, %s::vector, %s)
            ON CONFLICT (chunk_id) DO NOTHING
            """,
            (chunk_id, content, embedding, psycopg2.extras.Json(metadata or {})),
        )
        cur.close()

    def search(self, table_name: str, query_embedding: list[float], top_k: int = 10) -> list[dict[str, Any]]:
        """向量相似度检索"""
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute(
            f"""
            SELECT chunk_id, content, metadata,
                   1 - (embedding <=> %s::vector) AS similarity
            FROM {table_name}
            ORDER BY embedding <=> %s::vector
            LIMIT %s
            """,
            (query_embedding, query_embedding, top_k),
        )
        rows = cur.fetchall()
        cur.close()
        return [dict(r) for r in rows]

    def delete(self, table_name: str, chunk_id: str):
        """删除向量"""
        cur = self.conn.cursor()
        cur.execute(f"DELETE FROM {table_name} WHERE chunk_id = %s", (chunk_id,))
        cur.close()

    def count(self, table_name: str) -> int:
        cur = self.conn.cursor()
        cur.execute(f"SELECT count(*) FROM {table_name}")
        n = cur.fetchone()[0]
        cur.close()
        return n


retriever = PgVectorRetriever()
