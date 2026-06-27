from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from services.auth_service import get_db
from services.community_service import community_service
import json

router = APIRouter()


def post_to_dict(post):
    try:
        images = json.loads(post.images)
    except:
        images = []
    return {
        "id": post.id,
        "title": post.title,
        "device_type": post.device_type,
        "fault_type": post.fault_type,
        "content": post.content,
        "images": images,
        "author_id": post.author_id,
        "author_name": post.author_name,
        "status": post.status,
        "likes": post.likes,
        "views": post.views,
        "created_at": post.created_at.isoformat() if post.created_at else None,
        "reviewed_at": post.reviewed_at.isoformat() if post.reviewed_at else None,
        "review_comment": post.review_comment
    }


@router.get("/list")
async def list_posts(
    device_type: str = None,
    fault_type: str = None,
    keyword: str = None,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    result = community_service.list_approved_posts(db, device_type, fault_type, keyword, page, page_size)
    return {
        "items": [post_to_dict(p) for p in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"]
    }


@router.get("/{post_id}")
async def get_post(post_id: int, db: Session = Depends(get_db)):
    post = community_service.get_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"post": post_to_dict(post)}


@router.post("/create")
async def create_post(
    title: str,
    device_type: str,
    fault_type: str,
    content: str,
    images: str = "[]",
    author_id: int = None,
    author_name: str = "匿名用户",
    db: Session = Depends(get_db)
):
    try:
        img_list = json.loads(images)
    except:
        img_list = []
    post = community_service.create_post(db, title, device_type, fault_type, content, img_list, author_id, author_name)
    return {"post_id": post.id, "post": post_to_dict(post)}


@router.get("/list/mine")
async def list_my_posts(
    author_id: int = None,
    status: str = None,
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    result = community_service.list_my_posts(db, author_id, status, page, page_size)
    return {
        "items": [post_to_dict(p) for p in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"]
    }


@router.post("/{post_id}/like")
async def like_post(post_id: int, db: Session = Depends(get_db)):
    post = community_service.like_post(db, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"success": True, "likes": post.likes}


@router.delete("/{post_id}")
async def delete_post(post_id: int, author_id: int = None, db: Session = Depends(get_db)):
    success = community_service.delete_post(db, post_id, author_id)
    if not success:
        raise HTTPException(status_code=404, detail="Post not found or no permission")
    return {"success": True}


@router.get("/admin/pending")
async def list_pending_posts(
    page: int = 1,
    page_size: int = 10,
    db: Session = Depends(get_db)
):
    result = community_service.list_pending_posts(db, page, page_size)
    return {
        "items": [post_to_dict(p) for p in result["items"]],
        "total": result["total"],
        "page": result["page"],
        "page_size": result["page_size"]
    }


@router.post("/admin/{post_id}/approve")
async def approve_post(
    post_id: int,
    reviewer_id: int = None,
    comment: str = "",
    db: Session = Depends(get_db)
):
    post = community_service.approve_post(db, post_id, reviewer_id, comment)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"success": True, "post": post_to_dict(post)}


@router.post("/admin/{post_id}/reject")
async def reject_post(
    post_id: int,
    reviewer_id: int = None,
    comment: str = "",
    db: Session = Depends(get_db)
):
    post = community_service.reject_post(db, post_id, reviewer_id, comment)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    return {"success": True, "post": post_to_dict(post)}
