from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from services.auth_service import get_db, oauth2_scheme, get_current_user
from services.guidance_service import guidance_service
from datetime import datetime

router = APIRouter()


def guidance_to_dict(guidance):
    return {
        "id": guidance.id,
        "title": guidance.title,
        "device_type": guidance.device_type,
        "fault_type": guidance.fault_type,
        "content": guidance.content,
        "source_type": guidance.source_type,
        "source_id": guidance.source_id,
        "author_id": guidance.author_id,
        "is_public": guidance.is_public,
        "status": guidance.status,
        "views": guidance.views,
        "likes": guidance.likes,
        "created_at": guidance.created_at.isoformat() if guidance.created_at else None,
        "updated_at": guidance.updated_at.isoformat() if guidance.updated_at else None
    }


def get_optional_current_user(
    request: Request,
    db: Session = Depends(get_db)
):
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header.replace('Bearer ', '')
    try:
        return get_current_user(db, token)
    except:
        return None


@router.post("/generate")
async def generate_guidance(device_type: str, fault_type: str, user_id: int = None, db: Session = Depends(get_db)):
    guidance, result = guidance_service.generate_guidance(device_type, fault_type, user_id)
    return {
        "guidance_id": None,
        "title": guidance.title,
        "content": guidance.content,
        "device_type": guidance.device_type,
        "fault_type": guidance.fault_type,
        "summary": result.get("summary", "")
    }


@router.post("/save")
async def save_guidance(
    title: str,
    device_type: str,
    fault_type: str,
    content: str,
    source_type: str = "llm_generated",
    user_id: int = None,
    current_user = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    from models.task import Guidance
    actual_user_id = current_user.id if current_user else user_id
    guidance = Guidance(
        title=title,
        device_type=device_type,
        fault_type=fault_type,
        content=content,
        source_type=source_type,
        author_id=actual_user_id,
        status="published"
    )
    saved = guidance_service.save_guidance(db, guidance)
    return {"guidance_id": saved.id, "guidance": guidance_to_dict(saved)}


@router.get("/{guidance_id}")
async def get_guidance(guidance_id: int, db: Session = Depends(get_db)):
    guidance = guidance_service.get_guidance(db, guidance_id)
    if not guidance:
        raise HTTPException(status_code=404, detail="Guidance not found")
    return {"guidance": guidance_to_dict(guidance)}


@router.get("/list/mine")
async def list_my_guidance(
    page: int = 1,
    page_size: int = 10,
    current_user = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.id if current_user else None
    result = guidance_service.list_my_guidance(db, user_id, page, page_size)
    return {
        "items": [guidance_to_dict(g) for g in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"]
    }


@router.get("/list/public")
async def list_public_guidance(
    device_type: str = None,
    fault_type: str = None,
    keyword: str = None,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    result = guidance_service.list_public_guidance(db, device_type, fault_type, keyword, page, page_size)
    return {
        "items": [guidance_to_dict(g) for g in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"]
    }


@router.delete("/{guidance_id}")
async def delete_guidance(
    guidance_id: int,
    current_user = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.id if current_user else None
    success = guidance_service.delete_guidance(db, guidance_id, user_id)
    if not success:
        raise HTTPException(status_code=404, detail="Guidance not found or no permission")
    return {"success": True}


@router.post("/{guidance_id}/public")
async def toggle_public(
    guidance_id: int,
    is_public: bool,
    current_user = Depends(get_optional_current_user),
    db: Session = Depends(get_db)
):
    user_id = current_user.id if current_user else None
    guidance = guidance_service.toggle_public(db, guidance_id, user_id, is_public)
    if not guidance:
        raise HTTPException(status_code=404, detail="Guidance not found or no permission")
    return {"success": True, "is_public": guidance.is_public}
