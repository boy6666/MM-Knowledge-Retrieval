"""
社区服务层
负责用户经验分享、审核、查询等业务逻辑
"""
from sqlalchemy.orm import Session
from models.task import CommunityPost
from datetime import datetime
import json


class CommunityService:
    def create_post(self, db: Session, title: str, device_type: str, fault_type: str,
                    content: str, images: list = None, author_id: int = None, author_name: str = "匿名用户"):
        post = CommunityPost(
            title=title,
            device_type=device_type,
            fault_type=fault_type,
            content=content,
            images=json.dumps(images or [], ensure_ascii=False),
            author_id=author_id,
            author_name=author_name,
            status="pending"
        )
        db.add(post)
        db.commit()
        db.refresh(post)
        return post
    
    def get_post(self, db: Session, post_id: int):
        post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
        if post and post.status == "approved":
            post.views += 1
            db.commit()
        return post
    
    def list_approved_posts(self, db: Session, device_type: str = None, fault_type: str = None,
                            keyword: str = None, page: int = 1, page_size: int = 10):
        query = db.query(CommunityPost).filter(CommunityPost.status == "approved")
        
        if device_type:
            query = query.filter(CommunityPost.device_type.like(f"%{device_type}%"))
        if fault_type:
            query = query.filter(CommunityPost.fault_type.like(f"%{fault_type}%"))
        if keyword:
            query = query.filter(
                (CommunityPost.title.like(f"%{keyword}%")) |
                (CommunityPost.content.like(f"%{keyword}%"))
            )
        
        total = query.count()
        items = query.order_by(CommunityPost.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}
    
    def list_my_posts(self, db: Session, author_id: int, status: str = None,
                      page: int = 1, page_size: int = 10):
        query = db.query(CommunityPost).filter(CommunityPost.author_id == author_id)
        
        if status:
            query = query.filter(CommunityPost.status == status)
        
        total = query.count()
        items = query.order_by(CommunityPost.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}
    
    def list_pending_posts(self, db: Session, page: int = 1, page_size: int = 10):
        query = db.query(CommunityPost).filter(CommunityPost.status == "pending")
        total = query.count()
        items = query.order_by(CommunityPost.created_at.asc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}
    
    def approve_post(self, db: Session, post_id: int, reviewer_id: int = None, comment: str = ""):
        post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
        if post:
            post.status = "approved"
            post.reviewed_at = datetime.utcnow()
            post.reviewer_id = reviewer_id
            post.review_comment = comment
            db.commit()
            return post
        return None
    
    def reject_post(self, db: Session, post_id: int, reviewer_id: int = None, comment: str = ""):
        post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
        if post:
            post.status = "rejected"
            post.reviewed_at = datetime.utcnow()
            post.reviewer_id = reviewer_id
            post.review_comment = comment
            db.commit()
            return post
        return None
    
    def like_post(self, db: Session, post_id: int):
        post = db.query(CommunityPost).filter(CommunityPost.id == post_id).first()
        if post:
            post.likes += 1
            db.commit()
            return post
        return None
    
    def delete_post(self, db: Session, post_id: int, author_id: int):
        post = db.query(CommunityPost).filter(
            CommunityPost.id == post_id,
            CommunityPost.author_id == author_id
        ).first()
        if post:
            db.delete(post)
            db.commit()
            return True
        return False
    
    def search_posts(self, db: Session, keyword: str, device_type: str = None,
                     page: int = 1, page_size: int = 10):
        query = db.query(CommunityPost).filter(CommunityPost.status == "approved")
        
        if device_type:
            query = query.filter(CommunityPost.device_type.like(f"%{device_type}%"))
        
        if keyword:
            query = query.filter(
                (CommunityPost.title.like(f"%{keyword}%")) |
                (CommunityPost.content.like(f"%{keyword}%")) |
                (CommunityPost.fault_type.like(f"%{keyword}%"))
            )
        
        total = query.count()
        items = query.order_by(CommunityPost.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}


community_service = CommunityService()
