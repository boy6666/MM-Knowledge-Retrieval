"""
BGE 文本向量化引擎
"""
import numpy as np
from sentence_transformers import SentenceTransformer
from config.settings import settings


class BGEEmbedder:
    """BGE-base-zh-v1.5 文本向量化"""

    def __init__(self):
        self._model: SentenceTransformer | None = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(
                settings.EMBEDDING_MODEL_PATH,
                device="cpu",
            )
        return self._model

    def encode(self, texts: str | list[str]) -> np.ndarray:
        """文本 → 向量 (768维)"""
        if isinstance(texts, str):
            texts = [texts]
        # BGE 需要加 instruction prefix
        texts = [f"为这个句子生成向量以用于检索: {t}" for t in texts]
        emb = self.model.encode(texts, normalize_embeddings=True)
        return emb

    def encode_query(self, query: str) -> np.ndarray:
        """查询文本 → 向量"""
        emb = self.model.encode(
            [query],
            normalize_embeddings=True,
            prompt_name="query",
        )
        return emb[0]

    @property
    def dim(self) -> int:
        return settings.EMBEDDING_DIM

    @property
    def is_loaded(self) -> bool:
        return self._model is not None


embedder = BGEEmbedder()
