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


class VectorServiceV2:
    def __init__(self):
        os.makedirs(settings.CHROMA_DB_PATH, exist_ok=True)
        self.chunks = []
        self.images = []
        self.chunk_map = {}
        self.image_map = {}
        self.chunk_docs = []
        self.image_docs = []
        self.data_version = "v1"
        self._load_data()

    def _load_data(self):
        v2_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "processed", "structured_data_v2.json"
        )
        v1_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "processed", "processed_chunks.json"
        )
        manual_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "processed", "manual_data.json"
        )
        xyy_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data", "processed", "dataxyy.json"
        )

        if os.path.exists(xyy_path):
            print(f"[VectorServiceV2] 加载新维修数据(dataxyy): {xyy_path}")
            self._load_manual_data(xyy_path)
            self.data_version = "manual"
        elif os.path.exists(v2_path):
            print(f"[VectorServiceV2] 加载V2结构化数据: {v2_path}")
            self._load_v2_data(v2_path)
            self.data_version = "v2"
        elif os.path.exists(manual_path):
            print(f"[VectorServiceV2] 加载手动维修数据: {manual_path}")
            self._load_manual_data(manual_path)
            self.data_version = "manual"
        elif os.path.exists(v1_path):
            print(f"[VectorServiceV2] V2数据不存在，降级加载V1数据: {v1_path}")
            self._load_v1_data(v1_path)
            self.data_version = "v1"
        else:
            print("[VectorServiceV2] 未找到任何数据文件")

    def _load_v2_data(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.chunks = data.get("chunks", [])
        self.images = data.get("images", [])

        for chunk in self.chunks:
            cid = chunk.get("chunk_id", chunk.get("id", ""))
            self.chunk_map[cid] = chunk
            self.chunk_docs.append(chunk.get("text_for_embedding", chunk.get("text_content", "")))

        for img in self.images:
            iid = img.get("img_id", img.get("id", ""))
            self.image_map[iid] = img
            self.image_docs.append(img.get("text_for_embedding", img.get("description", "")))

        print(f"[VectorServiceV2] 已加载 {len(self.chunks)} 个文本块, {len(self.images)} 张图片")

    def _load_v1_data(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            all_chunks = json.load(f)

        for chunk in all_chunks:
            if chunk.get("type") == "text":
                cid = chunk.get("id", "")
                v2_chunk = {
                    "chunk_id": cid,
                    "type": "text",
                    "source_type": chunk.get("source_type", ""),
                    "chapter_tree": [chunk.get("title", "")],
                    "page_start": chunk.get("page", 0),
                    "page_end": chunk.get("page", 0),
                    "title": chunk.get("title", ""),
                    "text_content": chunk.get("content", ""),
                    "torque_list": [],
                    "gap_standard": [],
                    "bolt_types": [],
                    "keywords": chunk.get("keywords", []),
                    "text_for_embedding": chunk.get("text_for_embedding", ""),
                    "strong_img_ids": chunk.get("image_ids", []),
                    "weak_img_ids": [],
                    "tags": chunk.get("tags", [])
                }
                self.chunks.append(v2_chunk)
                self.chunk_map[cid] = v2_chunk
                self.chunk_docs.append(chunk.get("text_for_embedding", ""))
            elif chunk.get("type") == "image":
                iid = chunk.get("id", "")
                v2_img = {
                    "img_id": iid,
                    "type": "image",
                    "source_type": chunk.get("source_type", ""),
                    "origin_page": chunk.get("page", 0),
                    "storage_path": chunk.get("image_filename", ""),
                    "full_path": chunk.get("image_path", ""),
                    "caption": chunk.get("title", ""),
                    "description": chunk.get("description", ""),
                    "img_type": chunk.get("image_type", "示意图"),
                    "components": chunk.get("components", ""),
                    "keywords": chunk.get("keywords", []),
                    "text_for_embedding": chunk.get("text_for_embedding", ""),
                    "tags": chunk.get("tags", []),
                    "belong_chunk_ids": chunk.get("related_text_ids", []),
                    "chapter_path": []
                }
                self.images.append(v2_img)
                self.image_map[iid] = v2_img
                self.image_docs.append(chunk.get("text_for_embedding", ""))

        print(f"[VectorServiceV2] V1数据已转换: {len(self.chunks)} 个文本块, {len(self.images)} 张图片")

    def _load_manual_data(self, path):
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        for item in data:
            cid = item.get("doc_id", "")
            chunk = {
                "chunk_id": cid,
                "type": "text",
                "source_type": "manual",
                "chapter_tree": [item.get("big_chapter", ""), item.get("sub_title", "")],
                "page_start": 0,
                "page_end": 0,
                "title": item.get("sub_title", ""),
                "text_content": item.get("operate_text", ""),
                "torque_list": [f"{p['param']}: {p['value']}" for p in item.get("spec_data", []) if '扭矩' in p.get('param', '')],
                "gap_standard": [f"{p['param']}: {p['value']}" for p in item.get("spec_data", []) if '间隙' in p.get('param', '')],
                "bolt_types": [],
                "keywords": [],
                "text_for_embedding": f"{item.get('big_chapter', '')} {item.get('sub_title', '')} {item.get('operate_text', '')}",
                "strong_img_ids": [img.get("img_id", "") for img in item.get("multimodal_images", [])],
                "weak_img_ids": [],
                "tags": [item.get("big_chapter", "")]
            }
            self.chunks.append(chunk)
            self.chunk_map[cid] = chunk
            self.chunk_docs.append(chunk.get("text_for_embedding", ""))

            for img in item.get("multimodal_images", []):
                iid = img.get("img_id", "")
                if iid and iid not in self.image_map:
                    v2_img = {
                        "img_id": iid,
                        "type": "image",
                        "source_type": "manual",
                        "origin_page": 0,
                        "storage_path": img.get("img_id", "") + ".png",
                        "full_path": "",
                        "caption": img.get("text_correspond", ""),
                        "description": img.get("img_annotations", ""),
                        "img_type": img.get("img_type", "实拍维修图"),
                        "components": "",
                        "keywords": img.get("retrieval_tag", []),
                        "text_for_embedding": f"{img.get('img_type', '')} {img.get('img_annotations', '')} {img.get('text_correspond', '')}",
                        "tags": [],
                        "belong_chunk_ids": [cid],
                        "chapter_path": [item.get("big_chapter", ""), item.get("sub_title", "")]
                    }
                    self.images.append(v2_img)
                    self.image_map[iid] = v2_img
                    self.image_docs.append(v2_img.get("text_for_embedding", ""))

        print(f"[VectorServiceV2] 手动维修数据已加载: {len(self.chunks)} 个文本块, {len(self.images)} 张图片")

    def search_chunks(self, query: str, k: int = 5, chapter_filter: str = None):
        if not self.chunk_docs:
            return []

        query_tokens = tokenize(query)
        idf = compute_idf(self.chunk_docs)
        query_tfidf = compute_tfidf(query_tokens, idf)

        similarities = []
        for i, doc in enumerate(self.chunk_docs):
            doc_tokens = tokenize(doc)
            doc_tfidf = compute_tfidf(doc_tokens, idf)
            sim = cosine_similarity(query_tfidf, doc_tfidf)
            similarities.append((i, sim))

        similarities.sort(key=lambda x: -x[1])

        results = []
        for i, sim in similarities[:k * 3]:
            chunk = self.chunks[i]

            if chapter_filter:
                chapter_path = " ".join(chunk.get("chapter_tree", []))
                if chapter_filter not in chapter_path:
                    sim *= 0.3

            similarity = max(0, min(100, int(sim * 100)))
            if similarity < 5:
                continue

            result = {
                "chunk_id": chunk.get("chunk_id"),
                "title": chunk.get("title", ""),
                "content": chunk.get("text_content", ""),
                "similarity": similarity,
                "source_type": chunk.get("source_type"),
                "chapter_tree": chunk.get("chapter_tree", []),
                "page_start": chunk.get("page_start"),
                "page_end": chunk.get("page_end"),
                "torque_list": chunk.get("torque_list", []),
                "gap_standard": chunk.get("gap_standard", []),
                "bolt_types": chunk.get("bolt_types", []),
                "tags": chunk.get("tags", []),
                "strong_images": self._get_images_by_ids(chunk.get("strong_img_ids", [])),
                "weak_images": self._get_images_by_ids(chunk.get("weak_img_ids", [])),
            }
            results.append(result)
            if len(results) >= k:
                break

        return results

    def search_images(self, query: str, k: int = 5, chapter_filter: str = None):
        if not self.image_docs:
            return []

        query_tokens = tokenize(query)
        idf = compute_idf(self.image_docs)
        query_tfidf = compute_tfidf(query_tokens, idf)

        similarities = []
        for i, doc in enumerate(self.image_docs):
            doc_tokens = tokenize(doc)
            doc_tfidf = compute_tfidf(doc_tokens, idf)
            sim = cosine_similarity(query_tfidf, doc_tfidf)
            similarities.append((i, sim))

        similarities.sort(key=lambda x: -x[1])

        results = []
        for i, sim in similarities[:k * 3]:
            img = self.images[i]

            caption = img.get("caption", "")
            desc = img.get("description", "")
            caption_score = 0
            for q_token in query_tokens:
                if q_token in caption:
                    caption_score += 0.05
                if q_token in desc:
                    caption_score += 0.02
            sim += caption_score

            if chapter_filter:
                chapter_path = " ".join(img.get("chapter_path", []))
                if chapter_filter not in chapter_path:
                    sim *= 0.5

            similarity = max(0, min(100, int(sim * 100)))
            if similarity < 5:
                continue

            img_filename = img.get("storage_path", img.get("image_filename", ""))
            result = {
                "img_id": img.get("img_id"),
                "title": img.get("caption", ""),
                "description": img.get("description", ""),
                "similarity": similarity,
                "source_type": img.get("source_type"),
                "origin_page": img.get("origin_page"),
                "img_type": img.get("img_type"),
                "components": img.get("components", ""),
                "tags": img.get("tags", []),
                "image_filename": img_filename,
                "image_url": f"/api/images/{img_filename}" if img_filename else None,
                "belong_chunks": self._get_chunks_by_ids(img.get("belong_chunk_ids", [])),
                "chapter_path": img.get("chapter_path", []),
            }
            results.append(result)
            if len(results) >= k:
                break

        return results

    def search_combined(self, query: str, k: int = 5):
        chunk_results = self.search_chunks(query, k=k)
        image_results = self.search_images(query, k=k)

        return {
            "chunks": chunk_results,
            "images": image_results,
            "version": self.data_version
        }

    def _get_images_by_ids(self, img_ids):
        result = []
        for img_id in img_ids:
            img = self.image_map.get(img_id)
            if img:
                img_filename = img.get("storage_path", img.get("image_filename", ""))
                result.append({
                    "img_id": img.get("img_id", img_id),
                    "caption": img.get("caption", ""),
                    "description": img.get("description", ""),
                    "img_type": img.get("img_type", ""),
                    "image_filename": img_filename,
                    "image_url": f"/api/images/{img_filename}" if img_filename else None,
                    "origin_page": img.get("origin_page"),
                })
        return result

    def _get_chunks_by_ids(self, chunk_ids):
        result = []
        for cid in chunk_ids:
            chunk = self.chunk_map.get(cid)
            if chunk:
                result.append({
                    "chunk_id": chunk.get("chunk_id", cid),
                    "title": chunk.get("title", ""),
                    "chapter_tree": chunk.get("chapter_tree", []),
                    "page_start": chunk.get("page_start"),
                })
        return result

    def get_chunk_detail(self, chunk_id: str):
        chunk = self.chunk_map.get(chunk_id)
        if not chunk:
            return None

        return {
            "chunk_id": chunk.get("chunk_id"),
            "title": chunk.get("title", ""),
            "content": chunk.get("text_content", ""),
            "chapter_tree": chunk.get("chapter_tree", []),
            "page_start": chunk.get("page_start"),
            "page_end": chunk.get("page_end"),
            "torque_list": chunk.get("torque_list", []),
            "gap_standard": chunk.get("gap_standard", []),
            "bolt_types": chunk.get("bolt_types", []),
            "tags": chunk.get("tags", []),
            "strong_images": self._get_images_by_ids(chunk.get("strong_img_ids", [])),
            "weak_images": self._get_images_by_ids(chunk.get("weak_img_ids", [])),
        }

    def get_image_detail(self, img_id: str):
        img = self.image_map.get(img_id)
        if not img:
            return None

        img_filename = img.get("storage_path", img.get("image_filename", ""))
        return {
            "img_id": img.get("img_id"),
            "caption": img.get("caption", ""),
            "description": img.get("description", ""),
            "img_type": img.get("img_type", ""),
            "components": img.get("components", ""),
            "origin_page": img.get("origin_page"),
            "image_filename": img_filename,
            "image_url": f"/api/images/{img_filename}" if img_filename else None,
            "tags": img.get("tags", []),
            "chapter_path": img.get("chapter_path", []),
            "belong_chunks": self._get_chunks_by_ids(img.get("belong_chunk_ids", [])),
        }

    def get_chapter_tree(self):
        chapters = set()
        for chunk in self.chunks:
            tree = tuple(chunk.get("chapter_tree", []))
            if tree:
                chapters.add(tree)
        return sorted(list(chapters))

    def suggest_chapter(self, query: str, top_k: int = 10):
        chunks = self.search_chunks(query, k=top_k)
        if not chunks:
            return None

        if len(chunks) < 2:
            return None

        chapter_counts = {}
        for chunk in chunks:
            tree = chunk.get("chapter_tree", [])
            if tree:
                root_chapter = tree[0]
                chapter_counts[root_chapter] = chapter_counts.get(root_chapter, 0) + 1

        if not chapter_counts:
            return None

        most_common = max(chapter_counts, key=chapter_counts.get)
        ratio = chapter_counts[most_common] / len(chunks)

        # 降低触发门槛，只要占比>=40%就触发
        if ratio < 0.4:
            return None

        first_result = chunks[0]
        first_tree = first_result.get("chapter_tree", [])
        is_first_root = len(first_tree) == 1 and first_tree[0] == most_common

        top_sim = first_result.get("similarity", 0)

        # 简化触发条件：只要匹配占比足够就触发
        should_suggest = True

        if not should_suggest:
            return None

        sub_chapters = set()
        for chunk in self.chunks:
            tree = chunk.get("chapter_tree", [])
            if tree and tree[0] == most_common:
                if len(tree) >= 2:
                    sub_chapters.add(tree[1])

        sub_chapter_list = sorted(list(sub_chapters), key=lambda x: (
            int(re.search(r'^(\d+)', x).group(1)) if re.search(r'^(\d+)', x) else 999,
            x
        ))

        if not sub_chapter_list:
            sub_chapter_list = [most_common]

        return {
            "root_chapter": most_common,
            "sub_chapters": sub_chapter_list,
            "match_ratio": ratio,
            "top_similarity": top_sim,
            "is_root_match": is_first_root,
            "suggestion_text": f"检测到您可能想了解「{most_common}」相关内容，请选择具体的子章节："
        }

    def count_chunks(self):
        return len(self.chunks)

    def count_images(self):
        return len(self.images)

    def reload(self):
        self.chunks = []
        self.images = []
        self.chunk_map = {}
        self.image_map = {}
        self.chunk_docs = []
        self.image_docs = []
        self._load_data()


vector_service_v2 = VectorServiceV2()
