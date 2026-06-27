from fastapi import APIRouter, UploadFile, File, Form
from services.vector_service import vector_service
from services.vector_service_v2 import VectorServiceV2
from services.llm_service import llm_service
import os

router = APIRouter()

vector_service_v2 = VectorServiceV2()


def use_v2_service():
    return vector_service_v2.data_version in ["v2", "manual"]

@router.post("/text")
async def text_search(query: str = Form(...), k: int = 10, include_images: bool = True, use_v2: bool = True):
    if use_v2 and use_v2_service():
        chunks = vector_service_v2.search_chunks(query, k=k)
        images = []
        if include_images:
            images = vector_service_v2.search_images(query, k=k)
        results = []
        for chunk in chunks:
            results.append({
                "id": chunk["chunk_id"],
                "type": "text",
                "title": chunk["title"],
                "content": chunk["content"],
                "similarity": chunk["similarity"],
                "source_type": chunk["source_type"],
                "chapter_tree": chunk["chapter_tree"],
                "page_start": chunk["page_start"],
                "page_end": chunk["page_end"],
                "torque_list": chunk["torque_list"],
                "gap_standard": chunk["gap_standard"],
                "strong_images": chunk["strong_images"],
                "weak_images": chunk["weak_images"],
                "tags": chunk["tags"],
            })
        for img in images:
            results.append({
                "id": img["img_id"],
                "type": "image",
                "title": img["title"],
                "content": img["description"],
                "similarity": img["similarity"],
                "source_type": img["source_type"],
                "origin_page": img["origin_page"],
                "image_url": img["image_url"],
                "image_filename": img["image_filename"],
                "img_type": img["img_type"],
                "chapter_path": img["chapter_path"],
                "belong_chunks": img["belong_chunks"],
                "tags": img["tags"],
            })
        total = len(results)
        suggestion = vector_service_v2.suggest_chapter(query)
        return {"query": query, "results": results, "total": total, "version": "v2", "suggestion": suggestion}
    
    results = vector_service.search(query, k=k, include_images=include_images)
    return {"query": query, "results": results, "total": len(results), "version": "v1"}


@router.get("/stats")
async def search_stats():
    if use_v2_service():
        return {
            "version": "v2",
            "total_chunks": len(vector_service_v2.chunks),
            "text_chunks": len(vector_service_v2.chunks),
            "image_chunks": len(vector_service_v2.images),
            "total_images": len(vector_service_v2.images),
        }
    return {
        "version": "v1",
        "total_chunks": vector_service.count(),
        "text_chunks": vector_service.count_text(),
        "image_chunks": vector_service.count_images(),
    }


@router.post("/images-only")
async def images_search(query: str = Form(...), k: int = 10):
    if use_v2_service():
        results = vector_service_v2.search_images(query, k=k)
        return {"query": query, "results": results, "total": len(results), "version": "v2"}
    
    results = vector_service.search_images(query, k=k)
    return {"query": query, "results": results, "total": len(results)}


@router.post("/text-only")
async def text_only_search(query: str = Form(...), k: int = 10):
    if use_v2_service():
        results = vector_service_v2.search_chunks(query, k=k)
        return {"query": query, "results": results, "total": len(results), "version": "v2"}
    
    results = vector_service.search_text(query, k=k)
    return {"query": query, "results": results, "total": len(results)}


@router.post("/image")
async def image_search(image: UploadFile = File(...)):
    image_path = f"./data/images/{image.filename}"
    os.makedirs("./data/images", exist_ok=True)
    
    with open(image_path, "wb") as buffer:
        buffer.write(image.file.read())
    
    analysis = llm_service.analyze_image(image_path)
    query = analysis.get("query", "")
    
    if query:
        if use_v2_service():
            chunks = vector_service_v2.search_chunks(query, k=10)
            images = vector_service_v2.search_images(query, k=10)
            results = []
            for c in chunks:
                results.append({**c, "id": c["chunk_id"], "type": "text"})
            for img in images:
                results.append({**img, "id": img["img_id"], "type": "image"})
            results.sort(key=lambda x: -x.get("similarity", 0))
            return {"analysis": analysis, "query": query, "results": results, "version": "v2"}
        
        results = vector_service.search(query)
        return {"analysis": analysis, "query": query, "results": results}
    
    return {"analysis": analysis}


@router.post("/hybrid")
async def hybrid_search(
    query: str = Form(None),
    image: UploadFile = File(None),
    k: int = 10,
    include_images: bool = True
):
    final_query = query or ""
    
    if image:
        image_path = f"./data/images/{image.filename}"
        os.makedirs("./data/images", exist_ok=True)
        with open(image_path, "wb") as buffer:
            buffer.write(image.file.read())
        
        analysis = llm_service.analyze_image(image_path)
        image_query = analysis.get("query", "")
        if image_query:
            final_query = f"{final_query} {image_query}".strip()
    
    if use_v2_service():
        chunks = vector_service_v2.search_chunks(final_query, k=k)
        images = vector_service_v2.search_images(final_query, k=k) if include_images else []
        results = []
        for c in chunks:
            results.append({**c, "id": c["chunk_id"], "type": "text"})
        for img in images:
            results.append({**img, "id": img["img_id"], "type": "image"})
        results.sort(key=lambda x: -x.get("similarity", 0))
        return {"query": final_query, "results": results[:k], "total": len(results), "version": "v2"}
    
    results = vector_service.search(final_query, k=k, include_images=include_images)
    return {"query": final_query, "results": results, "total": len(results)}


@router.get("/chunk/{chunk_id}")
async def get_chunk_detail(chunk_id: str):
    if use_v2_service():
        detail = vector_service_v2.get_chunk_detail(chunk_id)
        if detail:
            return {"data": detail, "version": "v2"}
    return {"detail": "Not found"}


@router.get("/chapter-tree")
async def get_chapter_tree():
    if use_v2_service():
        chapters = {}
        for chunk in vector_service_v2.chunks:
            tree = chunk.get("chapter_tree", [])
            if tree:
                current = chapters
                for i, level in enumerate(tree):
                    if level not in current:
                        current[level] = {"_chunk_ids": [], "_children": {}}
                    if i == len(tree) - 1:
                        current[level]["_chunk_ids"].append(chunk.get("chunk_id"))
                    current = current[level]["_children"]
        
        def build_tree(d, depth=0):
            result = []
            for key, val in sorted(d.items()):
                node = {
                    "title": key,
                    "level": depth,
                    "chunk_count": len(val.get("_chunk_ids", [])),
                    "children": build_tree(val.get("_children", {}), depth + 1)
                }
                result.append(node)
            return result
        
        return {"tree": build_tree(chapters), "version": "v2"}
    return {"tree": [], "version": "v1"}


@router.get("/suggest")
async def get_suggestions(query: str):
    if use_v2_service():
        suggestion = vector_service_v2.suggest_chapter(query)
        return {"suggestion": suggestion, "version": "v2"}
    return {"suggestion": None, "version": "v1"}