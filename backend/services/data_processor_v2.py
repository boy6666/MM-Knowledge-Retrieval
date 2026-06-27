"""
版面坐标绑定 + 章节语义分块 + 图文强关联的数据处理服务
基于版面分析和空间位置实现精准图文绑定
"""

import os
import re
import json
import fitz
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT_DIR = os.path.dirname(BASE_DIR)
DEFAULT_PDF_PATH = os.path.join(ROOT_DIR, "摩托车发动机维修手册.pdf")
DEFAULT_JSON_PATH = os.path.join(ROOT_DIR, "data.json")
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "processed")
IMAGE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "images")


@dataclass
class TextBlock:
    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    font_size: float = 0
    font_name: str = ""
    is_bold: bool = False


@dataclass
class ImageBlock:
    page: int
    x0: float
    y0: float
    x1: float
    y1: float
    xref: int
    filename: str = ""
    path: str = ""
    area: float = 0


@dataclass
class ChapterNode:
    level: int
    title: str
    page_start: int
    page_end: int = 0
    y_start: float = 0
    y_end: float = 0
    children: List['ChapterNode'] = field(default_factory=list)
    parent: Optional['ChapterNode'] = None
    chunk_id: str = ""


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


def clean_text(text):
    text = text.replace('\r', '\n')
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r'[ \t]+', ' ', text)
    return text.strip()


def extract_page_blocks(page) -> Tuple[List[TextBlock], List[ImageBlock]]:
    text_blocks = []
    image_blocks = []
    
    blocks = page.get_text("dict")["blocks"]
    for block in blocks:
        if block["type"] == 0:
            bbox = block["bbox"]
            lines_text = []
            max_font_size = 0
            font_names = set()
            is_bold = False
            
            for line in block["lines"]:
                line_text = ""
                for span in line["spans"]:
                    line_text += span["text"]
                    if span["size"] > max_font_size:
                        max_font_size = span["size"]
                    font_names.add(span["font"])
                    if "Bold" in span["font"] or "bold" in span["font"]:
                        is_bold = True
                lines_text.append(line_text)
            
            text_content = "\n".join(lines_text).strip()
            if text_content:
                text_blocks.append(TextBlock(
                    page=page.number + 1,
                    x0=bbox[0],
                    y0=bbox[1],
                    x1=bbox[2],
                    y1=bbox[3],
                    text=text_content,
                    font_size=max_font_size,
                    font_name=",".join(font_names),
                    is_bold=is_bold
                ))
    
    page_images = page.get_images(full=True)
    for img_info in page_images:
        xref = img_info[0]
        img_rects = page.get_image_rects(xref)
        if not img_rects:
            continue
        
        rect = img_rects[0]
        area = rect.width * rect.height
        
        if area < 3000:
            continue
        
        image_blocks.append(ImageBlock(
            page=page.number + 1,
            x0=rect.x0,
            y0=rect.y0,
            x1=rect.x1,
            y1=rect.y1,
            xref=xref,
            area=area
        ))
    
    text_blocks.sort(key=lambda b: (b.y0, b.x0))
    image_blocks.sort(key=lambda b: b.y0)
    
    return text_blocks, image_blocks


CHAPTER_PATTERNS = [
    (1, re.compile(r'^[一二三四五六七八九十]+、')),
    (2, re.compile(r'^\d+\.\d+\s')),
    (3, re.compile(r'^[（(][一二三四五六七八九十]+[）)]')),
    (4, re.compile(r'^[（(]\d+[）)]')),
]

CAPTION_KEYWORDS = ['图', '图', '示意图', '装配图', '零件图', '图示', '详见图', '如图所示']

TORQUE_PATTERN = re.compile(r'(\d+[±~\-]\d*(?:\.\d+)?)\s*N[·•]m')
GAP_PATTERN = re.compile(r'(\d+(?:\.\d+)?\s*[~～\-]\s*\d+(?:\.\d+)?)\s*(?:mm|毫米)')
BOLT_PATTERN = re.compile(r'M\d+[×x]\d+')


def detect_chapter_level(text: str) -> Optional[int]:
    text = text.strip()
    for level, pattern in CHAPTER_PATTERNS:
        if pattern.match(text):
            return level
    return None


def is_caption_text(text: str) -> bool:
    text = text.strip()
    if len(text) > 100:
        return False
    for kw in CAPTION_KEYWORDS:
        if kw in text:
            return True
    if re.match(r'^图\s*[\d一二三四五六七八九十]+', text):
        return True
    return False


def extract_torque_values(text: str) -> List[str]:
    return TORQUE_PATTERN.findall(text)


def extract_gap_values(text: str) -> List[str]:
    return GAP_PATTERN.findall(text)


def extract_bolt_types(text: str) -> List[str]:
    return list(set(BOLT_PATTERN.findall(text)))


def build_chapter_tree(all_text_blocks: List[TextBlock]) -> List[ChapterNode]:
    root = []
    stack = []
    
    for block in all_text_blocks:
        level = detect_chapter_level(block.text)
        if level is None:
            continue
        
        title = block.text.strip()
        
        node = ChapterNode(
            level=level,
            title=title,
            page_start=block.page,
            y_start=block.y0
        )
        
        while stack and stack[-1].level >= level:
            popped = stack.pop()
            popped.page_end = block.page
            popped.y_end = block.y0
        
        if stack:
            stack[-1].children.append(node)
            node.parent = stack[-1]
        else:
            root.append(node)
        
        stack.append(node)
    
    for node in stack:
        node.page_end = all_text_blocks[-1].page if all_text_blocks else node.page_start
        node.y_end = 9999
    
    if len(root) > 1:
        l1_titles = [n.title for n in root if n.level == 1]
        title_counts = Counter(l1_titles)
        repeated_titles = {t for t, c in title_counts.items() if c > 1}
        
        if repeated_titles:
            last_occurrence = {}
            for i, node in enumerate(root):
                if node.level == 1 and node.title in repeated_titles:
                    last_occurrence[node.title] = i
            
            first_repeated_idx = min(last_occurrence.values())
            root = root[first_repeated_idx:]
    
    return root


def get_chapter_path(node: ChapterNode) -> List[str]:
    path = []
    current = node
    while current:
        path.insert(0, current.title)
        current = current.parent
    return path


def find_containing_chapter(page: int, y: float, chapter_root: List[ChapterNode]) -> Optional[ChapterNode]:
    best_match = None
    best_level = 0
    
    def traverse(nodes):
        nonlocal best_match, best_level
        for node in nodes:
            if node.page_start <= page <= node.page_end:
                if node.page_start == page and node.y_start > y:
                    continue
                if node.page_end == page and node.y_end < y:
                    continue
                if node.level > best_level:
                    best_match = node
                    best_level = node.level
                if node.children:
                    traverse(node.children)
    
    traverse(chapter_root)
    return best_match


def associate_images_with_captions(
    text_blocks: List[TextBlock],
    image_blocks: List[ImageBlock],
    page_height: float
) -> Dict[int, List[TextBlock]]:
    img_captions = defaultdict(list)
    
    for idx, img in enumerate(image_blocks):
        img_center_y = (img.y0 + img.y1) / 2
        
        candidates = []
        for tb in text_blocks:
            if not is_caption_text(tb.text):
                continue
            
            dist = abs(tb.y0 - img.y1)
            if tb.y0 >= img.y1 - 20 and tb.y0 <= img.y1 + 300:
                candidates.append((dist, tb))
            elif tb.y1 < img.y0 and img.y0 - tb.y1 < 200:
                candidates.append((dist, tb))
        
        candidates.sort(key=lambda x: x[0])
        img_captions[idx] = [tb for _, tb in candidates[:3]]
    
    return img_captions


def analyze_image_with_ai(image_path, surrounding_text=""):
    try:
        from services.llm_service import llm_service
        
        prompt = f"""请分析这张摩托车发动机维修手册的图片。
图片周边文字：{surrounding_text[:300]}

请返回以下信息（JSON格式）：
1. description: 图片内容的详细描述（100字左右）
2. keywords: 5-10个相关关键词（用逗号分隔）
3. type: 图片类型（如：示意图、零件图、装配图、流程图、电路图等）
4. components: 图中包含的主要部件名称（用逗号分隔）
5. caption: 图注标题（简短概括）

只返回JSON，不要其他内容。"""
        
        messages = [
            {"role": "system", "content": "你是一个专业的机械工程图像分析专家，擅长识别发动机维修手册中的各种图示。"},
            {"role": "user", "content": prompt}
        ]
        
        response = llm_service.chat(messages)
        content = response.get("response", "")
        
        try:
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
            "components": "",
            "caption": ""
        }
    except Exception as e:
        return {
            "description": f"图片分析失败: {str(e)}",
            "keywords": [],
            "type": "示意图",
            "components": "",
            "caption": ""
        }


def process_pdf_with_layout(pdf_path, use_ai=True, progress_callback=None):
    doc = fitz.open(pdf_path)
    
    all_text_blocks = []
    all_image_blocks = []
    page_heights = {}
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        page_heights[page_num + 1] = page.rect.height
        
        text_blocks, image_blocks = extract_page_blocks(page)
        all_text_blocks.extend(text_blocks)
        
        for ib in image_blocks:
            all_image_blocks.append(ib)
        
        if progress_callback:
            progress_callback(f"版面解析: {page_num+1}/{len(doc)}页")
    
    chapter_root = build_chapter_tree(all_text_blocks)
    
    chunks = []
    images = []
    
    chunk_counter = [0]
    def assign_chunk_ids(nodes):
        for node in nodes:
            chunk_counter[0] += 1
            node.chunk_id = f"c{chunk_counter[0]:04d}"
            assign_chunk_ids(node.children)
    
    assign_chunk_ids(chapter_root)
    
    page_image_map = defaultdict(list)
    for idx, img in enumerate(all_image_blocks):
        page_image_map[img.page].append((idx, img))
    
    img_global_idx = 0
    for page_num in range(1, len(doc) + 1):
        page = doc[page_num - 1]
        page_imgs = page_image_map.get(page_num, [])
        
        page_text_blocks = [tb for tb in all_text_blocks if tb.page == page_num]
        captions_map = associate_images_with_captions(
            page_text_blocks,
            [img for _, img in page_imgs],
            page_heights.get(page_num, 800)
        )
        
        for local_idx, (global_idx, img) in enumerate(page_imgs):
            img_global_idx += 1
            
            xref = img.xref
            try:
                base_image = doc.extract_image(xref)
                image_bytes = base_image["image"]
                image_ext = base_image["ext"]
            except:
                continue
            
            if len(image_bytes) < 3000:
                continue
            
            image_filename = f"pdf_page{page_num:03d}_img{img_global_idx:02d}.{image_ext}"
            image_path = os.path.join(IMAGE_DIR, image_filename)
            os.makedirs(IMAGE_DIR, exist_ok=True)
            with open(image_path, "wb") as f:
                f.write(image_bytes)
            
            chapter = find_containing_chapter(page_num, img.y0, chapter_root)
            chapter_path = get_chapter_path(chapter) if chapter else []
            
            caption_tbs = captions_map.get(local_idx, [])
            caption_text = " ".join([tb.text for tb in caption_tbs]) if caption_tbs else ""
            
            surrounding_text_parts = []
            for tb in page_text_blocks:
                if abs(tb.y0 - img.y0) < 500:
                    surrounding_text_parts.append(tb.text)
            surrounding_text = " ".join(surrounding_text_parts)[:300]
            
            ai_result = {}
            if use_ai:
                ai_result = analyze_image_with_ai(image_path, surrounding_text + caption_text)
            
            ai_description = ai_result.get("description", "")
            ai_keywords = ai_result.get("keywords", [])
            if isinstance(ai_keywords, str):
                ai_keywords = [k.strip() for k in ai_keywords.split(',') if k.strip()]
            ai_type = ai_result.get("type", "示意图")
            ai_components = ai_result.get("components", "")
            ai_caption = ai_result.get("caption", "")
            
            final_caption = ai_caption or caption_text or f"第{page_num}页插图"
            
            image_description = ai_description or caption_text or f"维修手册第{page_num}页插图"
            
            all_keywords = list(set(extract_keywords(surrounding_text) + ai_keywords))
            
            vector_text = f"""图片：{image_description}
设备类型：摩托车发动机
页码：第{page_num}页
图片类型：{ai_type}
图注：{final_caption}
周边文字：{surrounding_text[:200]}
相关部件：{ai_components}
章节路径：{' / '.join(chapter_path)}
相关关键词：{', '.join(all_keywords[:10])}
图片描述：{image_description}
"""
            
            image_data = {
                "img_id": f"img{img_global_idx:04d}",
                "type": "image",
                "source_type": "manual",
                "origin_page": page_num,
                "storage_path": image_filename,
                "full_path": image_path,
                "bbox": {"x0": img.x0, "y0": img.y0, "x1": img.x1, "y1": img.y1},
                "caption": final_caption,
                "caption_text_ocr": caption_text,
                "img_text_ocr": [],
                "description": image_description,
                "img_type": ai_type,
                "components": ai_components,
                "keywords": all_keywords[:15],
                "text_for_embedding": vector_text.strip(),
                "tags": ["维修手册", "插图", "摩托车发动机", ai_type] + all_keywords[:5],
                "ai_analyzed": True if ai_result else False,
                "belong_chunk_ids": [],
                "chapter_path": chapter_path
            }
            images.append(image_data)
        
        if progress_callback:
            progress_callback(f"图片处理: {page_num}/{len(doc)}页")
    
    chapter_chunks = []
    
    def create_chunks_from_chapter(node: ChapterNode):
        chapter_path = get_chapter_path(node)
        
        chapter_text_blocks = []
        for tb in all_text_blocks:
            if tb.page < node.page_start or tb.page > node.page_end:
                continue
            if tb.page == node.page_start and tb.y0 < node.y_start:
                continue
            if tb.page == node.page_end and tb.y0 > node.y_end:
                continue
            chapter_text_blocks.append(tb)
        
        full_text = "\n\n".join([tb.text for tb in chapter_text_blocks])
        full_text = clean_text(full_text)
        
        if not full_text or len(full_text) < 20:
            for child in node.children:
                create_chunks_from_chapter(child)
            return
        
        torque_list = extract_torque_values(full_text)
        gap_list = extract_gap_values(full_text)
        bolt_list = extract_bolt_types(full_text)
        keywords = extract_keywords(full_text)
        
        vector_text = f"""标题：{node.title}
章节路径：{' / '.join(chapter_path)}
起始页码：第{node.page_start}页
设备类型：摩托车发动机
扭矩参数：{', '.join(torque_list)}
间隙标准：{', '.join(gap_list)}
螺栓型号：{', '.join(bolt_list)}
相关关键词：{', '.join(keywords[:10])}
内容：
{full_text}
"""
        
        strong_img_ids = []
        weak_img_ids = []
        
        img_global_idx = 0
        for img in images:
            img_page = img["origin_page"]
            img_y = img["bbox"]["y0"]
            
            if img_page < node.page_start or img_page > node.page_end:
                continue
            if img_page == node.page_start and img_y < node.y_start - 50:
                continue
            if img_page == node.page_end and img_y > node.y_end + 50:
                continue
            
            is_strong = False
            for tb in chapter_text_blocks:
                if tb.page == img_page:
                    dist = abs(tb.y0 - img_y)
                    if dist < 200:
                        is_strong = True
                        break
            
            if is_strong:
                strong_img_ids.append(img["img_id"])
            else:
                weak_img_ids.append(img["img_id"])
        
        chunk_data = {
            "chunk_id": node.chunk_id,
            "type": "text",
            "source_type": "manual",
            "chapter_tree": chapter_path,
            "page_start": node.page_start,
            "page_end": node.page_end,
            "title": node.title,
            "text_content": full_text,
            "torque_list": torque_list,
            "gap_standard": gap_list,
            "bolt_types": bolt_list,
            "keywords": keywords,
            "text_for_embedding": vector_text.strip(),
            "strong_img_ids": strong_img_ids,
            "weak_img_ids": weak_img_ids,
            "tags": ["维修手册", "摩托车发动机"] + chapter_path + keywords[:5]
        }
        chapter_chunks.append(chunk_data)
        
        for img_id in strong_img_ids + weak_img_ids:
            for img in images:
                if img["img_id"] == img_id:
                    if node.chunk_id not in img["belong_chunk_ids"]:
                        img["belong_chunk_ids"].append(node.chunk_id)
        
        for child in node.children:
            create_chunks_from_chapter(child)
    
    for root_node in chapter_root:
        create_chunks_from_chapter(root_node)
    
    doc.close()
    
    return chapter_chunks, images, chapter_root


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
        
        chunk_id = f"case_{case_id}"
        img_id = f"case_img_{case_id}"
        
        text_chunks.append({
            "chunk_id": chunk_id,
            "type": "text",
            "source_type": "case",
            "case_id": case_id,
            "chapter_tree": [category, fault_name],
            "title": fault_name,
            "category": category,
            "text_content": f"故障描述：{fault_desc}\n故障原因：{cause}\n维修步骤：{repair_step}",
            "keywords": keywords,
            "text_for_embedding": text_for_embedding,
            "strong_img_ids": [img_id] if image_desc else [],
            "weak_img_ids": [],
            "tags": tags
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
                "img_id": img_id,
                "type": "image",
                "source_type": "case",
                "case_id": case_id,
                "caption": fault_name + " - 故障图片",
                "category": category,
                "description": image_desc,
                "key_features": key_features,
                "keywords": keywords,
                "text_for_embedding": image_text,
                "img_type": "故障特征图",
                "tags": tags + ["故障图片", "特征识别"],
                "belong_chunk_ids": [chunk_id],
                "chapter_path": [category, fault_name]
            })
        
        if progress_callback and idx % 10 == 0:
            progress_callback(f"处理故障案例: {idx+1}/{len(cases)}")
    
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
            progress_callback("[1/4] 正在解析PDF版面+章节分块...")
        pdf_chunks, pdf_images, chapter_root = process_pdf_with_layout(pdf_path, use_ai=use_ai, progress_callback=progress_callback)
        
        if progress_callback:
            progress_callback("[3/4] 正在处理故障案例...")
        case_chunks, case_images = process_fault_cases(json_path, progress_callback)
        
        all_chunks = pdf_chunks + case_chunks
        all_images = pdf_images + case_images
        
        output_data = {
            "version": "2.0",
            "description": "版面坐标绑定+章节语义分块+图文强关联数据",
            "stats": {
                "total_chunks": len(all_chunks),
                "total_images": len(all_images),
                "pdf_chunks": len(pdf_chunks),
                "pdf_images": len(pdf_images),
                "case_chunks": len(case_chunks),
                "case_images": len(case_images),
                "ai_analyzed_images": sum(1 for img in pdf_images if img.get("ai_analyzed"))
            },
            "chunks": all_chunks,
            "images": all_images
        }
        
        if progress_callback:
            progress_callback("[4/4] 正在写入文件...")
        output_path = os.path.join(OUTPUT_DIR, "structured_data_v2.json")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        return {
            "success": True,
            "stats": output_data["stats"],
            "output_path": output_path,
            "use_ai": use_ai
        }
    except Exception as e:
        import traceback
        return {"success": False, "error": str(e), "traceback": traceback.format_exc()}