from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from services.auth_service import get_db, oauth2_scheme, get_current_user
from models.user import User
from models.task import CommunityPost
from models.knowledge import Knowledge
from services.vector_service_v2 import vector_service_v2

router = APIRouter(tags=["admin"])

def get_admin_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    user = get_current_user(db, token)
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Not authorized")
    return user

@router.get("/users")
async def list_users(current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    users = db.query(User).order_by(User.created_at.desc()).all()
    return {"users": [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "created_at": u.created_at.isoformat() if u.created_at else None
        } for u in users
    ]}

@router.post("/users/{user_id}/role")
async def update_user_role(
    user_id: int,
    role: str,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    if role not in ["user", "admin"]:
        raise HTTPException(status_code=400, detail="Invalid role")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot change own role")
    
    user.role = role
    db.commit()
    return {"success": True}

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot delete self")
    
    db.delete(user)
    db.commit()
    return {"success": True}

@router.get("/stats")
async def get_admin_stats(current_user: User = Depends(get_admin_user), db: Session = Depends(get_db)):
    total_users = db.query(User).count()
    total_posts = db.query(CommunityPost).count()
    pending_posts = db.query(CommunityPost).filter(CommunityPost.status == "pending").count()
    total_knowledge = db.query(Knowledge).count()
    
    knowledge_count = len(vector_service_v2.chunks) if vector_service_v2 else 0
    image_count = len(vector_service_v2.images) if vector_service_v2 else 0
    
    return {
        "data": {
            "total_users": total_users,
            "total_posts": total_posts,
            "pending_posts": pending_posts,
            "total_knowledge": knowledge_count + image_count
        }
    }

@router.post("/knowledge/{knowledge_id}/reject")
async def reject_knowledge(
    knowledge_id: int,
    comment: str = "",
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    
    knowledge.status = "rejected"
    db.commit()
    return {"success": True}

@router.delete("/knowledge/{knowledge_id}")
async def delete_knowledge(
    knowledge_id: int,
    current_user: User = Depends(get_admin_user),
    db: Session = Depends(get_db)
):
    knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    
    db.delete(knowledge)
    db.commit()
    return {"success": True}
