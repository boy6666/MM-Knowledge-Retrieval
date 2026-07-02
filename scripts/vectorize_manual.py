"""
将 dataxyy.json 中的手册数据向量化后写入 pgvector
"""
import json
import sys
import os

# 确保能找到 ai-core 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "ai-core"))
os.chdir(os.path.join(os.path.dirname(__file__), "..", "ai-core"))

from config.settings import settings
from vector.embedder import embedder
from vector.retriever import retriever

# 读取 dataxyy.json
data_path = os.path.join(os.path.dirname(__file__), "..", "dataxyy.json")
with open(data_path, "r", encoding="utf-8") as f:
    entries = json.load(f)

print(f"共加载 {len(entries)} 条手册数据")

# 确保 pgvector 表存在
retriever.ensure_extension()
retriever.ensure_table("embeddings")

# 逐条向量化并插入
count = 0
for entry in entries:
    chunk_id = entry.get("doc_id", f"manual_{count:04d}")

    # 构建向量化文本
    big_chapter = entry.get("big_chapter", "")
    sub_title = entry.get("sub_title", "")
    operate_text = entry.get("operate_text", "")
    risk_tips = entry.get("risk_tips", "")

    # 拼接规格参数
    spec_text = ""
    for s in entry.get("spec_data", []):
        param = s.get("param", "")
        value = s.get("value", "")
        if param and value:
            spec_text += f"{param}: {value}; "

    # 拼接完整文本
    content_parts = [big_chapter, sub_title, operate_text]
    if spec_text:
        content_parts.append(f"规格参数: {spec_text}")
    if risk_tips:
        content_parts.append(f"注意事项: {risk_tips}")
    full_content = "\n".join(p for p in content_parts if p)

    if not full_content.strip():
        continue

    # 向量化
    embedding = embedder.encode(full_content)[0].tolist()

    # 插入 pgvector
    metadata = {
        "big_chapter": big_chapter,
        "sub_title": sub_title,
        "source": "维修手册",
    }
    retriever.insert("embeddings", chunk_id, full_content, embedding, metadata)
    count += 1

    if count % 10 == 0:
        print(f"  已处理 {count}/{len(entries)}")

print(f"\n完成！共向量化并插入 {count} 条数据到 pgvector")
print(f"当前向量总数: {retriever.count('embeddings')}")
