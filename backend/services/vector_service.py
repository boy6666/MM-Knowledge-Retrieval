import os
import re
import math
import json
from config import settings


def tokenize(text):
    tokens = []
    i = 0
    while i < len(text):
        if '\u4e00' <= text[i] <= '\u9fff':
            tokens.append(text[i])
            i += 1
        elif text[i].isalnum():
            j = i
            while j < len(text) and text[j].isalnum():
                j += 1
            tokens.append(text[i:j].lower())
            i = j
        else:
            i += 1
    return tokens


def compute_tf(tokens):
    tf = {}
    for token in tokens:
        tf[token] = tf.get(token, 0) + 1
    return tf


def compute_idf(documents):
    idf = {}
    num_docs = len(documents)
    for doc in documents:
        unique_tokens = set(tokenize(doc))
        for token in unique_tokens:
            idf[token] = idf.get(token, 0) + 1
    for token in idf:
        idf[token] = math.log((num_docs + 1) / (idf[token] + 1)) + 1
    return idf


def compute_tfidf(tokens, idf):
    tf = compute_tf(tokens)
    tfidf = {}
    max_tf = max(tf.values()) if tf else 1
    for token in tf:
        tfidf[token] = (tf[token] / max_tf) * idf.get(token, 1)
    return tfidf


def cosine_similarity(vec1, vec2):
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum(vec1[t] * vec2[t] for t in intersection)
    sum1 = sum(vec1[t] ** 2 for t in vec1)
    sum2 = sum(vec2[t] ** 2 for t in vec2)
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    if not denominator:
        return 0.0
    return numerator / denominator


class VectorService:
    def __init__(self):
        os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
        self.documents = []
        self.metadata = []
        self.all_chunks = []
        self._load_processed_data()

    def _load_processed_data(self):
        processed_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "processed", "processed_chunks.json"
        )
        if os.path.exists(processed_path):
            print(f"[VectorService] 正在加载处理好的数据: {processed_path}")
            with open(processed_path, 'r', encoding='utf-8') as f:
                self.all_chunks = json.load(f)
            
            for chunk in self.all_chunks:
                self.documents.append(chunk.get("text_for_embedding", chunk.get("content", "")))
                meta = {
                    "id": chunk.get("id"),
                    "type": chunk.get("type", "text"),
                    "source_type": chunk.get("source_type"),
                    "source_file": chunk.get("source_file"),
                    "title": chunk.get("title"),
                    "content": chunk.get("content", ""),
                    "tags": chunk.get("tags", []),
                }
                if chunk.get("type") == "image":
                    meta["image_filename"] = chunk.get("image_filename")
                    meta["image_path"] = chunk.get("image_path")
                    meta["description"] = chunk.get("description")
                    meta["page"] = chunk.get("page")
                else:
                    meta["page"] = chunk.get("page")
                    meta["image_ids"] = chunk.get("image_ids", [])
                self.metadata.append(meta)
            
            print(f"[VectorService] 已加载 {len(self.all_chunks)} 个数据块")
            print(f"  - 文本块: {len([c for c in self.all_chunks if c['type']=='text'])}")
            print(f"  - 图片块: {len([c for c in self.all_chunks if c['type']=='image'])}")

    def add_document(self, file_path: str):
        from langchain_community.document_loaders import PyPDFLoader
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )
        loader = PyPDFLoader(file_path)
        documents = loader.load()
        split_docs = text_splitter.split_documents(documents)
        for i, doc in enumerate(split_docs):
            self.documents.append(doc.page_content)
            self.metadata.append({"source": file_path, "chunk": i, "type": "text"})
        return len(split_docs)

    def add_text(self, text: str, metadata: dict = None):
        from langchain_text_splitters import RecursiveCharacterTextSplitter
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=50,
            length_function=len,
        )
        docs = text_splitter.create_documents([text])
        meta = metadata or {}
        meta["type"] = meta.get("type", "text")
        for doc in docs:
            self.documents.append(doc.page_content)
            self.metadata.append(meta)
        return len(docs)

    def search(self, query: str, k: int = 5, include_images: bool = True):
        if not self.documents:
            return []

        query_tokens = tokenize(query)
        idf = compute_idf(self.documents)
        query_tfidf = compute_tfidf(query_tokens, idf)

        similarities = []
        for i, doc in enumerate(self.documents):
            doc_tokens = tokenize(doc)
            doc_tfidf = compute_tfidf(doc_tokens, idf)
            sim = cosine_similarity(query_tfidf, doc_tfidf)
            similarities.append((i, sim))

        similarities.sort(key=lambda x: -x[1])

        output = []
        for i, sim in similarities[:k * 3]:
            meta = self.metadata[i]
            if not include_images and meta.get("type") == "image":
                continue
            similarity = max(0, min(100, int(sim * 100)))
            result = {
                "id": meta.get("id"),
                "type": meta.get("type", "text"),
                "title": meta.get("title", ""),
                "content": meta.get("content", self.documents[i]),
                "similarity": similarity,
                "source_type": meta.get("source_type"),
                "source_file": meta.get("source_file"),
                "page": meta.get("page"),
                "tags": meta.get("tags", []),
            }
            if meta.get("type") == "image":
                result["image_filename"] = meta.get("image_filename")
                result["image_path"] = meta.get("image_path")
                result["image_url"] = f"/api/images/{meta.get('image_filename', '')}" if meta.get("image_filename") else None
                result["description"] = meta.get("description")
            else:
                result["image_ids"] = meta.get("image_ids", [])
                result["related_images"] = self._get_related_images(meta.get("image_ids", []))
            output.append(result)
            if len(output) >= k:
                break

        return output

    def _get_related_images(self, image_ids):
        related = []
        for chunk in self.all_chunks:
            if chunk.get("id") in image_ids and chunk.get("type") == "image":
                related.append({
                    "id": chunk.get("id"),
                    "image_filename": chunk.get("image_filename"),
                    "image_path": chunk.get("image_path"),
                    "image_url": f"/api/images/{chunk.get('image_filename', '')}",
                    "title": chunk.get("title"),
                    "description": chunk.get("description"),
                    "page": chunk.get("page"),
                })
        return related

    def search_images(self, query: str, k: int = 5):
        image_indices = [i for i, meta in enumerate(self.metadata) if meta.get("type") == "image"]
        
        if not image_indices:
            return []
        
        query_tokens = tokenize(query)
        idf = compute_idf(self.documents)
        query_tfidf = compute_tfidf(query_tokens, idf)
        
        similarities = []
        for i in image_indices:
            doc = self.documents[i]
            doc_tokens = tokenize(doc)
            doc_tfidf = compute_tfidf(doc_tokens, idf)
            sim = cosine_similarity(query_tfidf, doc_tfidf)
            similarities.append((i, sim))
        
        similarities.sort(key=lambda x: -x[1])
        
        output = []
        for i, sim in similarities[:k]:
            meta = self.metadata[i]
            similarity = max(0, min(100, int(sim * 100)))
            result = {
                "id": meta.get("id"),
                "type": meta.get("type", "image"),
                "title": meta.get("title", ""),
                "content": meta.get("content", self.documents[i]),
                "similarity": similarity,
                "source_type": meta.get("source_type"),
                "source_file": meta.get("source_file"),
                "page": meta.get("page"),
                "tags": meta.get("tags", []),
                "image_filename": meta.get("image_filename"),
                "image_path": meta.get("image_path"),
                "image_url": f"/api/images/{meta.get('image_filename', '')}" if meta.get("image_filename") else None,
                "description": meta.get("description"),
            }
            output.append(result)
        
        return output

    def search_text(self, query: str, k: int = 5):
        results = self.search(query, k=k, include_images=True)
        return [r for r in results if r["type"] == "text"]

    def get_chunk_by_id(self, chunk_id: str):
        for chunk in self.all_chunks:
            if chunk.get("id") == chunk_id:
                return chunk
        return None

    def get_chunks_by_source(self, source_file: str = None, source_type: str = None):
        results = []
        for chunk in self.all_chunks:
            if source_file and chunk.get("source_file") != source_file:
                continue
            if source_type and chunk.get("source_type") != source_type:
                continue
            results.append(chunk)
        return results

    def count(self):
        return len(self.documents)

    def count_text(self):
        return len([c for c in self.all_chunks if c.get("type") == "text"])

    def count_images(self):
        return len([c for c in self.all_chunks if c.get("type") == "image"])

    def reload(self):
        """重新加载处理好的数据，用于重新处理数据后刷新内存"""
        self.documents = []
        self.metadata = []
        self.all_chunks = []
        self._load_processed_data()


vector_service = VectorService()
