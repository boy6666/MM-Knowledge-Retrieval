"""
对话相关接口：多轮对话、语音识别、视频处理、图片生成
"""
import os
import uuid
import tempfile
from fastapi import APIRouter, UploadFile, File, Form
from fastapi.responses import JSONResponse
from services.conversation_service import conversation_service
from services.llm_service import llm_service
from services.vector_service import vector_service
from utils.response import success, fail

router = APIRouter()


@router.post("/new")
async def new_conversation():
    """创建新对话"""
    conv = conversation_service.create_conversation()
    return success({
        "conversation_id": conv.id,
        "message_count": 0
    })


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    """获取对话详情"""
    conv = conversation_service.get_conversation(conversation_id)
    if not conv:
        return fail("对话不存在", code=404)
    return success({
        "conversation_id": conv.id,
        "messages": conv.messages,
        "created_at": conv.created_at,
        "last_active": conv.last_active
    })


@router.delete("/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """删除对话"""
    conversation_service.delete_conversation(conversation_id)
    return success({"message": "对话已删除"})


@router.post("/{conversation_id}/chat")
async def chat(
    conversation_id: str,
    message: str = Form(None),
    image: UploadFile = File(None),
    video: UploadFile = File(None),
    audio: UploadFile = File(None)
):
    """
    发送消息（支持文字、图片、视频、语音）
    返回：文本回复 + 相关图片推荐
    """
    conv = conversation_service.get_conversation(conversation_id)
    if not conv:
        return fail("对话不存在", code=404)

    full_message = message or ""
    media_url = ""
    media_type = "text"

    if audio:
        audio_text = await recognize_speech(audio)
        full_message = f"{full_message} {audio_text}".strip()
        media_type = "audio"

    if image:
        image_path = await save_upload_file(image)
        media_url = f"/api/images/{image.filename}"
        media_type = "image"
        analysis = llm_service.analyze_image(image_path)
        if analysis.get("description"):
            full_message = f"{full_message} 图片分析: {analysis['description']}".strip()

    if video:
        video_path = await save_upload_file(video)
        media_url = f"/api/images/{video.filename}"
        media_type = "video"
        frame_path = extract_video_frame(video_path)
        if frame_path:
            analysis = llm_service.analyze_image(frame_path)
            if analysis.get("description"):
                full_message = f"{full_message} 视频帧分析: {analysis['description']}".strip()

    if not full_message:
        return fail("请输入消息或上传文件", code=400)

    conv.add_message("user", full_message, media_type, media_url)

    from langchain_core.messages import HumanMessage, SystemMessage
    context = conv.get_context(max_messages=10)
    messages = []
    for msg in context:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(SystemMessage(content=msg["content"]))

    system_msg = SystemMessage(content="""你是一个专业的设备检修专家助手。
请根据用户的问题，提供准确、专业的检修建议。
回答要清晰、有条理，包括故障分析、检修步骤、注意事项等。
如果涉及图片分析，请结合图片内容进行诊断。""")
    messages.insert(0, system_msg)

    response = llm_service.chat(messages)
    ai_response = response.get("response", "")

    related_images = []
    if full_message:
        search_results = vector_service.search(full_message, k=8, include_images=True)
        for result in search_results:
            if result["type"] == "image" and result.get("image_url"):
                related_images.append({
                    "id": result["id"],
                    "title": result["title"],
                    "image_url": result["image_url"],
                    "description": result.get("description", ""),
                    "source_type": result.get("source_type", "")
                })
            elif result.get("related_images"):
                for img in result["related_images"]:
                    if img.get("image_url") and img["image_url"] not in [i["image_url"] for i in related_images]:
                        related_images.append({
                            "id": img["id"],
                            "title": img.get("title", ""),
                            "image_url": img["image_url"],
                            "description": img.get("description", ""),
                            "source_type": "manual"
                        })

    conv.add_message("assistant", ai_response, "text", "")

    return success({
        "conversation_id": conversation_id,
        "response": ai_response,
        "related_images": related_images[:5],
        "provider": response.get("provider", "unknown"),
        "difficulty": response.get("difficulty", "unknown")
    })


@router.post("/speech-to-text")
async def speech_to_text(audio: UploadFile = File(...)):
    """语音转文字"""
    text = await recognize_speech(audio)
    if text.startswith("语音识别失败") or text.startswith("未安装"):
        return fail(text, code=500)
    return success({"text": text})


@router.post("/video-analyze")
async def video_analyze(video: UploadFile = File(...)):
    """视频分析（提取帧并分析）"""
    video_path = await save_upload_file(video)
    frame_path = extract_video_frame(video_path)
    
    if frame_path:
        analysis = llm_service.analyze_image(frame_path)
        return success({
            "description": analysis.get("description", ""),
            "query": analysis.get("query", ""),
            "frame_image_url": f"/api/images/{os.path.basename(frame_path)}"
        })
    return fail("视频帧提取失败，可能未安装OpenCV库", code=500)


@router.post("/image-generate")
async def image_generate(prompt: str = Form(...)):
    """AI文生图"""
    try:
        image_url = generate_image(prompt)
        return success({
            "prompt": prompt,
            "image_url": image_url
        })
    except Exception as e:
        return fail(f"图片生成失败: {str(e)}", code=500)


async def recognize_speech(audio_file: UploadFile):
    """语音识别"""
    try:
        import speech_recognition as sr
        recognizer = sr.Recognizer()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp:
            temp.write(await audio_file.read())
            temp_path = temp.name
        
        with sr.AudioFile(temp_path) as source:
            audio = recognizer.record(source)
            text = recognizer.recognize_google(audio, language="zh-CN")
        
        os.unlink(temp_path)
        return text
    except ImportError:
        return "未安装语音识别库，请运行: pip install SpeechRecognition"
    except Exception as e:
        return f"语音识别失败: {str(e)}"


async def save_upload_file(file: UploadFile):
    """保存上传文件"""
    save_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "images")
    os.makedirs(save_dir, exist_ok=True)
    
    file_path = os.path.join(save_dir, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    return file_path


def extract_video_frame(video_path):
    """从视频提取帧"""
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            return None
        
        success, frame = cap.read()
        cap.release()
        
        if success:
            frame_filename = f"video_frame_{uuid.uuid4().hex[:8]}.png"
            frame_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "data", "images", frame_filename
            )
            cv2.imwrite(frame_path, frame)
            return frame_path
        return None
    except ImportError:
        return None
    except Exception as e:
        return None


def generate_image(prompt):
    """生成图片（占位实现）"""
    import requests
    try:
        return f"https://picsum.photos/seed/{prompt}/800/600"
    except:
        return f"https://via.placeholder.com/800x600?text={prompt[:20]}"
