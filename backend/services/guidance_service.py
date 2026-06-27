"""
检修方案服务层
负责检修方案的生成、保存、查询等业务逻辑
"""
from sqlalchemy.orm import Session
from models.task import Guidance
# 移除不必要的LLM服务导入，减少初始化延迟
# from services.llm_service import llm_service
from datetime import datetime


class GuidanceService:
    def generate_guidance(self, device_type: str, fault_type: str, user_id: int = None):
        # 延迟导入LLM服务，仅在需要时加载
        from services.llm_service import llm_service
        result = llm_service.generate_guide(device_type, fault_type)
        
        content = result.get("full_content", "")
        if not content:
            steps = result.get("steps", [])
            content_parts = [f"# {device_type} - {fault_type}检修方案\n"]
            for i, step in enumerate(steps, 1):
                content_parts.append(f"\n## 步骤{i}: {step.get('title', '')}\n")
                content_parts.append(step.get("description", ""))
            content = "\n".join(content_parts)
        
        guidance = Guidance(
            title=f"{device_type} - {fault_type}检修方案",
            device_type=device_type,
            fault_type=fault_type,
            content=content,
            source_type="llm_generated",
            author_id=user_id,
            status="draft"
        )
        
        return guidance, result
    
    def save_guidance(self, db: Session, guidance: Guidance):
        guidance.status = "published"
        guidance.updated_at = datetime.utcnow()
        db.add(guidance)
        db.commit()
        db.refresh(guidance)
        return guidance
    
    def get_guidance(self, db: Session, guidance_id: int):
        guidance = db.query(Guidance).filter(Guidance.id == guidance_id).first()
        if guidance:
            guidance.views += 1
            db.commit()
        return guidance
    
    def list_my_guidance(self, db: Session, user_id: int, page: int = 1, page_size: int = 10):
        query = db.query(Guidance).filter(Guidance.status != "draft")
        if user_id:
            query = query.filter(Guidance.author_id == user_id)
        else:
            # 未登录用户：显示匿名创建的方案（author_id为NULL）
            query = query.filter(Guidance.author_id.is_(None))
        total = query.count()
        items = query.order_by(Guidance.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}
    
    def list_public_guidance(self, db: Session, device_type: str = None, fault_type: str = None, 
                             keyword: str = None, page: int = 1, page_size: int = 10):
        query = db.query(Guidance).filter(Guidance.is_public == True, Guidance.status == "published")
        
        if device_type:
            query = query.filter(Guidance.device_type.like(f"%{device_type}%"))
        if fault_type:
            query = query.filter(Guidance.fault_type.like(f"%{fault_type}%"))
        if keyword:
            query = query.filter(
                (Guidance.title.like(f"%{keyword}%")) |
                (Guidance.content.like(f"%{keyword}%"))
            )
        
        total = query.count()
        items = query.order_by(Guidance.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        return {"items": items, "total": total, "page": page, "page_size": page_size}
    
    def delete_guidance(self, db: Session, guidance_id: int, user_id: int):
        if user_id:
            guidance = db.query(Guidance).filter(
                Guidance.id == guidance_id,
                Guidance.author_id == user_id
            ).first()
        else:
            guidance = db.query(Guidance).filter(
                Guidance.id == guidance_id,
                Guidance.author_id == None
            ).first()
        if guidance:
            db.delete(guidance)
            db.commit()
            return True
        return False
    
    def toggle_public(self, db: Session, guidance_id: int, user_id: int, is_public: bool):
        guidance = db.query(Guidance).filter(
            Guidance.id == guidance_id,
            Guidance.author_id == user_id
        ).first()
        if guidance:
            guidance.is_public = is_public
            guidance.updated_at = datetime.utcnow()
            db.commit()
            return guidance
        return None


guidance_service = GuidanceService()
