"""
PDF解析脚本 - 按照dataxyy.json格式重新拆分PDF
"""
import os
import re
import json
import fitz  # PyMuPDF
from PIL import Image
import io

# PDF文件路径
PDF_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "uploads", "摩托车发动机维修手册.pdf")
OUTPUT_JSON_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "processed", "pdf_parsed_dataxyy.json")
OUTPUT_IMAGES_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "images")


def extract_text_and_images_from_pdf(pdf_path):
    """从PDF提取文本和图片"""
    doc = fitz.open(pdf_path)
    all_pages_data = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # 提取文本
        text = page.get_text()
        
        # 提取图片
        images = []
        image_list = page.get_images(full=True)
        
        for img_idx, img_info in enumerate(image_list):
            xref = img_info[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            # 保存图片
            img_filename = f"pdf_page{page_num+1:03d}_img{img_idx+1:02d}.{image_ext}"
            img_path = os.path.join(OUTPUT_IMAGES_PATH, img_filename)
            
            with open(img_path, "wb") as f:
                f.write(image_bytes)
            
            images.append({
                "img_id": f"P{page_num+1}_img{img_idx+1}",
                "img_filename": img_filename,
                "img_type": "PDF提取图片"
            })
        
        all_pages_data.append({
            "page_num": page_num + 1,
            "text": text,
            "images": images
        })
    
    doc.close()
    return all_pages_data


def identify_chapter_structure(text):
    """识别章节结构"""
    # 大章节模式: 一、火花塞  二、起动电机 等
    big_chapter_pattern = r'^([一二三四五六七八九十]+、[^\n]+)'
    
    # 子标题模式: 1.1 拆卸火花塞  2.1 起动电机装配部件清单 等
    sub_title_pattern = r'^(\d+\.\d+\s+[^\n]+)'
    
    big_chapters = re.findall(big_chapter_pattern, text, re.MULTILINE)
    sub_titles = re.findall(sub_title_pattern, text, re.MULTILINE)
    
    return big_chapters, sub_titles


def extract_spec_data(text):
    """提取规格参数"""
    spec_data = []
    
    # 扭矩参数模式
    torque_patterns = [
        r'(\d+[±～\-]\d+\s*N·m)',
        r'(\d+\s*±\s*\d+\s*N·m)',
        r'拧紧[^：:]*[：:]\s*(\d+[±～\-]\d+\s*N·m)',
    ]
    
    for pattern in torque_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if match:
                spec_data.append({"param": "拧紧扭矩", "value": match})
    
    # 间隙参数模式
    gap_patterns = [
        r'间隙[^：:]*[：:]\s*(\d+[．.～\-]+\d+\s*mm)',
        r'(\d+[．.～\-]+\d+\s*mm)[^\n]*间隙',
    ]
    
    for pattern in gap_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if match:
                spec_data.append({"param": "间隙标准", "value": match})
    
    # 压力参数
    pressure_patterns = [
        r'(\d+[～\-]+\d+\s*kPa)',
    ]
    
    for pattern in pressure_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if match:
                spec_data.append({"param": "压力标准", "value": match})
    
    return spec_data


def extract_risk_tips(text):
    """提取风险提示/注意事项"""
    risk_tips = []
    
    # 注意事项模式
    note_patterns = [
        r'注意[：:]\s*([^\n]+)',
        r'警示[：:]\s*([^\n]+)',
        r'警告[：:]\s*([^\n]+)',
        r'提示[：:]\s*([^\n]+)',
    ]
    
    for pattern in note_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if match and len(match) > 5:
                risk_tips.append(match.strip())
    
    return risk_tips


def parse_pdf_to_dataxyy_format(pdf_path):
    """按照dataxyy格式解析PDF"""
    print(f"开始解析PDF: {pdf_path}")
    
    # 提取所有页面数据
    pages_data = extract_text_and_images_from_pdf(pdf_path)
    
    print(f"共提取 {len(pages_data)} 页数据")
    
    # 定义章节映射
    chapter_mapping = {
        "1": "一、火花塞",
        "2": "二、起动电机",
        "3": "三、发动机",
        "4": "四、气缸头与气门",
        "5": "五、气缸与活塞",
        "6": "六、右曲轴箱盖、离合器、机油泵、水泵",
        "7": "七、左曲轴箱盖、磁电机转子离合器",
        "8": "八、传动装置",
        "9": "九、曲轴与平衡轴",
    }
    
    # ID前缀映射
    id_prefix_mapping = {
        "1": "S",   # Spark plug
        "2": "M",   # Motor
        "3": "E",   # Engine
        "4": "CH",  # Cylinder head
        "5": "CP",  # Cylinder piston
        "6": "RC",  # Right cover
        "7": "LC",  # Left cover
        "8": "T",   # Transmission
        "9": "CB",  # Crankshaft balance
    }
    
    result = []
    doc_counters = {k: 1 for k in id_prefix_mapping.keys()}
    
    # 按页面处理
    current_big_chapter = ""
    current_sub_title = ""
    current_content = ""
    current_page_num = 1
    
    for page in pages_data:
        text = page['text']
        page_num = page['page_num']
        
        # 识别子标题
        sub_title_matches = re.findall(r'^(\d+)\.(\d+)\s+([^\n]+)', text, re.MULTILINE)
        
        for match in sub_title_matches:
            chapter_num = match[0]
            sub_num = match[1]
            sub_name = match[2].strip()
            
            sub_title = f"{chapter_num}.{sub_num} {sub_name}"
            big_chapter = chapter_mapping.get(chapter_num, "")
            
            if not big_chapter:
                continue
            
            # 找到该子标题在文本中的位置
            sub_title_full = f"{chapter_num}.{sub_num} {sub_name}"
            start_idx = text.find(sub_title_full)
            
            if start_idx >= 0:
                # 提取从该位置到下一个子标题的内容
                remaining_text = text[start_idx + len(sub_title_full):]
                next_sub_idx = re.search(r'\d+\.\d+\s+', remaining_text)
                
                if next_sub_idx:
                    content = remaining_text[:next_sub_idx.start()]
                else:
                    content = remaining_text
                
                # 清理内容
                content = content.strip()
                content = re.sub(r'No\. \d+ / \d+', '', content)
                content = re.sub(r'摩托车发动机维修手册', '', content)
                content = re.sub(r'\n+', '\n', content)
                content = content.strip()
                
                if len(content) < 10:
                    continue
                
                # 提取规格参数
                spec_data = extract_spec_data(content)
                
                # 提取风险提示
                risk_tips = extract_risk_tips(content)
                
                # 关联图片
                multimodal_images = []
                for img in page['images']:
                    multimodal_images.append({
                        "img_id": img['img_id'],
                        "img_type": "PDF提取图片",
                        "img_annotations": f"来自第{page_num}页",
                        "text_correspond": f"对应{sub_title}操作",
                        "retrieval_tag": [sub_name.split()[0] if sub_name else "维修"]
                    })
                
                # 生成文档ID
                doc_id_prefix = id_prefix_mapping.get(chapter_num, f"X{chapter_num}")
                doc_id = f"{doc_id_prefix}{doc_counters[chapter_num]:03d}"
                doc_counters[chapter_num] += 1
                
                # 构建结果
                result.append({
                    "doc_id": doc_id,
                    "big_chapter": big_chapter,
                    "sub_title": sub_title,
                    "operate_text": content[:800] if len(content) > 800 else content,
                    "spec_data": spec_data,
                    "risk_tips": risk_tips,
                    "related_parts": [],
                    "multimodal_images": multimodal_images[:3] if multimodal_images else [],
                    "source_page": page_num
                })
    
    print(f"共生成 {len(result)} 个文档块")
    return result


def main():
    print("=" * 50)
    print("PDF解析脚本 - 按dataxyy格式拆分")
    print("=" * 50)
    
    if not os.path.exists(PDF_PATH):
        print(f"PDF文件不存在: {PDF_PATH}")
        return
    
    # 确保输出目录存在
    os.makedirs(OUTPUT_IMAGES_PATH, exist_ok=True)
    os.makedirs(os.path.dirname(OUTPUT_JSON_PATH), exist_ok=True)
    
    # 解析PDF
    result = parse_pdf_to_dataxyy_format(PDF_PATH)
    
    # 保存结果
    with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\n解析完成!")
    print(f"- 输出JSON: {OUTPUT_JSON_PATH}")
    print(f"- 图片目录: {OUTPUT_IMAGES_PATH}")
    print(f"- 共生成 {len(result)} 个文档块")


if __name__ == "__main__":
    main()