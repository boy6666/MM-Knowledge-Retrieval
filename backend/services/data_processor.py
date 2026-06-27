"""
AI增强的数据处理服务：使用AI分析PDF图片内容，智能拆分和关联数据
"""

import os
import re
import json
import fitz
from collections import Counter

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BASE_DIR)
DEFAULT_PDF_PATH = os.path.join(ROOT_DIR, "摩托车发动机维修手册.pdf")
DEFAULT_JSON_PATH = os.path.join(ROOT_DIR, "data.json")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "processed")
IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "images")
CHUNK_SIZE = 600
CHUNK_OVERLAP = 80


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


def extract_keywords(text):
    try:
        import jieba
        words = jieba.lcut(text)
        stop_words = {'的', '是', '在', '有', '和', '了', '我', '你', '他', '她', '它', '这', '那', '很', '都', '就', '也', '要', '会', '可以', '能', '不', '去', '来', '上', '下', '大', '小', '多', '少', '一个', '一些', '什么', '怎么', '因为', '所以', '但是', '如果', '虽然', '还是', '或者', '以及', '等等', '比如', '例如', '包括', '通过', '根据', '关于', '对于', '至于', '按照', '为了', '由于', '鉴于', '随着', '经过', '进行', '执行', '实现', '完成', '达到', '得到', '获得', '取得', '发生', '出现', '产生', '形成', '造成', '导致', '引起', '使得', '成为', '变为', '变成', '当作', '作为', '用于', '用来', '以便', '以免', '得以', '可以', '可能', '应该', '应当', '必须', '需要', '值得', '能够', '愿意', '乐意', '希望', '想要', '打算', '计划', '准备', '决定', '同意', '拒绝', '接受', '允许', '禁止', '建议', '提议', '推荐', '要求', '请求', '申请', '询问', '回答', '说明', '解释', '介绍', '描述', '表达', '表示', '指出', '强调', '提醒', '警告', '注意', '重视', '忽视', '忘记', '记得', '想起', '知道', '了解', '认识', '熟悉', '掌握', '学会', '懂得', '理解', '明白', '清楚', '确定', '肯定', '否定', '怀疑', '相信', '认为', '以为', '觉得', '感到', '感觉', '看起来', '听起来', '闻起来', '尝起来', '摸起来'}
        
        filtered = [w for w in words if len(w) > 1 and w not in stop_words]
        counter = Counter(filtered)
        return [word for word, _ in counter.most_common(20)]
    except ImportError:
        tokens = tokenize(text)
        counter = Counter(tokens)
        return [word for word, _ in counter.most_common(20)]


def extract_text_from_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    pages = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text()
        if text.strip():
            pages.append({"page": page_num + 1, "text": text.strip()})
    doc.close()
    return pages


def clean_text(text):
    text = text.replace('\r', '\n')
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def split_into_chunks(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    paragraphs = re.split(r'\n\s*\n', text)
    chunks = []
    current_chunk = ""
    for para in paragraphs:
        para = para.strip()
        if not para:
            continue
        if len(current_chunk) + len(para) + 2 <= chunk_size:
            current_chunk += para + "\n\n"
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            if len(para) > chunk_size:
                for i in range(0, len(para), chunk_size - overlap):
                    chunks.append(para[i:i + chunk_size])
                current_chunk = ""
            else:
                if overlap > 0 and chunks:
                    last = chunks[-1]
                    overlap_text = last[-overlap:] if len(last) > overlap else last
                    current_chunk = overlap_text + "\n" + para + "\n\n"
                else:
                    current_chunk = para + "\n\n"
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks


def process_pdf_text(pdf_path, progress_callback=None):
    pages = extract_text_from_pdf(pdf_path)
    all_chunks = []
    chunk_id = 0
    
    for page_info in pages:
        page_num = page_info["page"]
        text = clean_text(page_info["text"])
        keywords = extract_keywords(text)
        
        chunks = split_into_chunks(text)
        
        for i, chunk in enumerate(chunks):
            chunk_id += 1
            lines = chunk.split('\n')
            title = lines[0].strip()[:50] if lines else f"第{page_num}页"
            
            vector_text = f"""标题：{title}
页码：第{page_num}页
设备类型：摩托车发动机
来源：摩托车发动机维修手册
相关关键词：{', '.join(keywords[:10])}
内容：
{chunk}
""".strip()
            
            all_chunks.append({
                "id": f"pdf_text_{chunk_id:04d}",
                "type": "text",
                "source_type": "manual",
                "source_file": os.path.basename(pdf_path),
                "page": page_num,
                "title": title,
                "content": chunk,
                "keywords": keywords[:10],
                "text_for_embedding": vector_text,
                "tags": ["维修手册", "摩托车发动机"] + keywords[:5],
                "image_ids": []
            })
        
        if progress_callback:
            progress_callback(f"处理PDF文本: {page_num}/41页")
    
    return all_chunks


def extract_surrounding_text(page, xref, full_text):
    try:
        img_rect = page.get_image_rects(xref)
        if not img_rect:
            return ""
        
        img_box = img_rect[0]
        tolerance = 50
        
        surrounding_rect = fitz.Rect(
            max(0, img_box.x0 - tolerance),
            max(0, img_box.y0 - tolerance),
            min(page.rect.width, img_box.x1 + tolerance),
            min(page.rect.height, img_box.y1 + tolerance * 2)
        )
        
        words = page.get_text("words")
        surrounding_words = []
        for word in words:
            word_rect = fitz.Rect(word[0], word[1], word[2], word[3])
            if surrounding_rect.intersects(word_rect):
                surrounding_words.append(word[4])
        
        if surrounding_words:
            return " ".join(surrounding_words)
        
        lines = full_text.split('\n')
        return "\n".join(lines[:5])
    except:
        lines = full_text.split('\n')
        return "\n".join(lines[:5])


def analyze_image_with_ai(image_path, surrounding_text=""):
    """使用AI分析图片内容，生成描述和关键词"""
    try:
        from services.llm_service import llm_service
        
        prompt = f"""请分析这张摩托车发动机维修手册的图片。
图片周边文字：{surrounding_text[:300]}

请返回以下信息（JSON格式）：
1. description: 图片内容的详细描述（100字左右）
2. keywords: 5-10个相关关键词（用逗号分隔）
3. type: 图片类型（如：示意图、零件图、装配图、流程图、电路图等）
4. components: 图中包含的主要部件名称（用逗号分隔）

只返回JSON，不要其他内容。"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的机械工程图像分析专家，擅长识别发动机维修手册中的各种图示。"},
            {"role": "user", "content": prompt}
        ]
        
        response = llm_service.chat(messages)
        content = response.get("response", "")
        
        try:
            import re
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                result = json.loads(json_match.group())
                return result
        except:
            pass
        
        return {
            "description": content[:200],
            "keywords": extract_keywords(content)[:10],
            "type": "示意图",
            "components": ""
        }
    except Exception as e:
        return {
            "description": f"图片分析失败: {str(e)}",
            "keywords": [],
            "type": "示意图",
            "components": ""
        }


def extract_images_from_pdf(pdf_path, output_dir, use_ai=True, progress_callback=None):
    os.makedirs(output_dir, exist_ok=True)
    doc = fitz.open(pdf_path)
    images = []
    image_id = 0
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_images = page.get_images(full=True)
        
        page_text = page.get_text()
        page_text_clean = clean_text(page_text)
        page_keywords = extract_keywords(page_text_clean)
        
        for img_index, img in enumerate(page_images):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            if len(image_bytes) < 3000:
                continue
            
            image_filename = f"pdf_page{page_num+1:03d}_img{img_index+1:02d}.{image_ext}"
            image_path = os.path.join(output_dir, image_filename)
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            
            image_id += 1
            
            img_rect = page.get_image_rects(xref)
            img_area = 0
            if img_rect:
                img_area = img_rect[0].width * img_rect[0].height
            
            surrounding_text = extract_surrounding_text(page, xref, page_text_clean)
            
            ai_result = {}
            if use_ai:
                ai_result = analyze_image_with_ai(image_path, surrounding_text)
            
            ai_description = ai_result.get("description", "")
            ai_keywords = ai_result.get("keywords", [])
            if isinstance(ai_keywords, str):
                ai_keywords = [k.strip() for k in ai_keywords.split(',') if k.strip()]
            ai_type = ai_result.get("type", "示意图")
            ai_components = ai_result.get("components", "")
            
            image_description = f"维修手册第{page_num+1}页插图"
            if ai_description:
                image_description = ai_description
            elif surrounding_text:
                image_description = f"{surrounding_text[:100]}..."
            
            all_keywords = list(set(page_keywords + ai_keywords))
            
            vector_text = f"""图片：{image_description}
设备类型：摩托车发动机
页码：第{page_num+1}页
图片类型：{ai_type}
周边文字：{surrounding_text[:200]}
相关部件：{ai_components}
相关关键词：{', '.join(all_keywords[:10])}
图片描述：{image_description}
"""
            
            images.append({
                "id": f"pdf_image_{image_id:04d}",
                "type": "image",
                "source_type": "manual",
                "source_file": os.path.basename(pdf_path),
                "page": page_num + 1,
                "image_filename": image_filename,
                "image_path": image_path,
                "file_size": len(image_bytes),
                "image_area": img_area,
                "image_type": ai_type,
                "components": ai_components,
                "title": f"第{page_num+1}页 - {image_description[:30]}",
                "description": image_description,
                "surrounding_text": surrounding_text,
                "keywords": all_keywords[:15],
                "text_for_embedding": vector_text.strip(),
                "tags": ["维修手册", "插图", "摩托车发动机", ai_type] + all_keywords[:5],
                "ai_analyzed": True if ai_result else False
            })
        
        if progress_callback:
            progress_callback(f"提取PDF图片: {page_num+1}/41页")
    
    doc.close()
    return images


def process_fault_cases(json_path, progress_callback=None):
    with open(json_path, 'r', encoding='utf-8') as f:
        cases = json.load(f)
    text_chunks = []
    image_chunks = []
    
    for idx, case in enumerate(cases):
        case_id = case.get("id", f"unknown_{idx}")
        fault_name = case.get("faultName", "")
        category = case.get("category", "")
        fault_desc = case.get("faultDesc", "")
        cause = case.get("cause", "")
        repair_step = case.get("repairStep", "")
        tags = case.get("tags", [])
        image_desc = case.get("imageFeatureDesc", "")
        key_features = case.get("keyFeaturePoints", "")
        
        all_text = f"{fault_name} {category} {fault_desc} {cause} {repair_step}"
        keywords = extract_keywords(all_text)
        
        text_for_embedding = f"""
故障名称：{fault_name}
故障类别：{category}
故障描述：{fault_desc}
故障原因：{cause}
维修步骤：{repair_step}
相关标签：{', '.join(tags)}
相关关键词：{', '.join(keywords[:10])}
        """.strip()
        
        text_chunks.append({
            "id": f"case_text_{case_id}",
            "type": "text",
            "source_type": "case",
            "source_file": os.path.basename(json_path),
            "case_id": case_id,
            "title": fault_name,
            "category": category,
            "content": f"故障描述：{fault_desc}\n故障原因：{cause}\n维修步骤：{repair_step}",
            "keywords": keywords,
            "text_for_embedding": text_for_embedding,
            "tags": tags,
            "related_image_id": f"case_image_{case_id}"
        })
        
        if image_desc or key_features:
            image_text = f"""
故障图片：{fault_name}
图片描述：{image_desc}
关键特征点：{key_features}
故障类别：{category}
相关标签：{', '.join(tags)}
相关关键词：{', '.join(keywords[:10])}
            """.strip()
            image_chunks.append({
                "id": f"case_image_{case_id}",
                "type": "image",
                "source_type": "case",
                "source_file": os.path.basename(json_path),
                "case_id": case_id,
                "title": fault_name + " - 故障图片",
                "category": category,
                "image_path": "",
                "description": image_desc,
                "key_features": key_features,
                "keywords": keywords,
                "text_for_embedding": image_text,
                "tags": tags + ["故障图片", "特征识别"],
                "related_text_id": f"case_text_{case_id}"
            })
        
        if progress_callback and idx % 10 == 0:
            progress_callback(f"处理故障案例: {idx+1}/{len(cases)}")
    
    return text_chunks, image_chunks


def associate_images_with_text(text_chunks, image_chunks):
    page_texts = {}
    for chunk in text_chunks:
        if chunk["source_type"] == "manual" and "page" in chunk:
            page = chunk["page"]
            if page not in page_texts:
                page_texts[page] = []
            page_texts[page].append(chunk["id"])
    
    for img in image_chunks:
        if img["source_type"] == "manual" and "page" in img:
            page = img["page"]
            related = page_texts.get(page, [])
            for p in [page-1, page+1]:
                related.extend(page_texts.get(p, []))
            img["related_text_ids"] = list(set(related))[:5]
    
    page_images = {}
    for img in image_chunks:
        if img["source_type"] == "manual" and "page" in img:
            page = img["page"]
            if page not in page_images:
                page_images[page] = []
            page_images[page].append(img["id"])
    
    for chunk in text_chunks:
        if chunk["source_type"] == "manual" and "page" in chunk:
            page = chunk["page"]
            chunk["image_ids"] = page_images.get(page, [])
    
    text_keywords_index = {}
    for chunk in text_chunks:
        for kw in chunk.get("keywords", []):
            if kw not in text_keywords_index:
                text_keywords_index[kw] = []
            text_keywords_index[kw].append(chunk["id"])
    
    for img in image_chunks:
        if "keywords" in img:
            keyword_matches = []
            for kw in img["keywords"]:
                keyword_matches.extend(text_keywords_index.get(kw, []))
            if keyword_matches:
                existing_related = img.get("related_text_ids", [])
                combined = list(set(existing_related + keyword_matches))[:8]
                img["related_text_ids"] = combined
    
    image_keywords_index = {}
    for img in image_chunks:
        for kw in img.get("keywords", []):
            if kw not in image_keywords_index:
                image_keywords_index[kw] = []
            image_keywords_index[kw].append(img["id"])
    
    for chunk in text_chunks:
        if "keywords" in chunk:
            keyword_matches = []
            for kw in chunk["keywords"]:
                keyword_matches.extend(image_keywords_index.get(kw, []))
            if keyword_matches:
                existing_images = chunk.get("image_ids", [])
                combined = list(set(existing_images + keyword_matches))[:5]
                chunk["image_ids"] = combined
    
    return text_chunks, image_chunks


def run_full_process(pdf_path=None, json_path=None, use_ai=True, progress_callback=None):
    pdf_path = pdf_path or DEFAULT_PDF_PATH
    json_path = json_path or DEFAULT_JSON_PATH
    
    if not os.path.exists(pdf_path):
        return {"success": False, "error": f"PDF不存在: {pdf_path}"}
    if not os.path.exists(json_path):
        return {"success": False, "error": f"JSON不存在: {json_path}"}
    
    try:
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        os.makedirs(IMAGE_DIR, exist_ok=True)
        
        if progress_callback:
            progress_callback("[1/4] 正在提取PDF文本...")
        pdf_text_chunks = process_pdf_text(pdf_path, progress_callback)
        
        if progress_callback:
            progress_callback(f"[2/4] 正在提取PDF图片{'（AI分析中）' if use_ai else ''}...")
        pdf_image_chunks = extract_images_from_pdf(pdf_path, IMAGE_DIR, use_ai=use_ai, progress_callback=progress_callback)
        
        if progress_callback:
            progress_callback("[3/4] 正在处理故障案例...")
        case_text_chunks, case_image_chunks = process_fault_cases(json_path, progress_callback)
        
        all_text_chunks = pdf_text_chunks + case_text_chunks
        all_image_chunks = pdf_image_chunks + case_image_chunks
        
        all_text_chunks, all_image_chunks = associate_images_with_text(
            all_text_chunks, all_image_chunks
        )
        
        if progress_callback:
            progress_callback("[4/4] 正在写入文件...")
        all_chunks = all_text_chunks + all_image_chunks
        output_path = os.path.join(OUTPUT_DIR, "processed_chunks.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(all_chunks, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "stats": {
                "total": len(all_chunks),
                "text": len(all_text_chunks),
                "image": len(all_image_chunks),
                "pdf_text": len(pdf_text_chunks),
                "pdf_image": len(pdf_image_chunks),
                "case_text": len(case_text_chunks),
                "case_image": len(case_image_chunks),
                "ai_analyzed_images": sum(1 for img in pdf_image_chunks if img.get("ai_analyzed"))
            },
            "output_path": output_path,
            "use_ai": use_ai
        }
    except Exception as e:
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}
