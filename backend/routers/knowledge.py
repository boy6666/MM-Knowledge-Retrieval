from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from services.auth_service import get_db
from services.vector_service import vector_service
from models.knowledge import Knowledge, Document
from datetime import datetime
import os

router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    title: str = Form(...),
    category: str = Form("manual"),
    device_type: str = Form(None),
    user_id: int = Form(None),
    db: Session = Depends(get_db)
):
    file_path = f"./data/uploads/{file.filename}"
    os.makedirs("./data/uploads", exist_ok=True)
    
    with open(file_path, "wb") as buffer:
        buffer.write(file.file.read())
    
    doc = Document(
        filename=file.filename,
        filepath=file_path,
        file_type=file.content_type,
        size=os.path.getsize(file_path),
        uploaded_by=user_id
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    if file.filename.lower().endswith(".pdf"):
        count = vector_service.add_document(file_path)
        knowledge = Knowledge(
            title=title,
            content=f"PDF文档已索引，共{count}个段落",
            category=category,
            source=file.filename,
            device_type=device_type,
            status="approved",
            creator_id=user_id
        )
        db.add(knowledge)
        db.commit()
        
        return {"document_id": doc.id, "knowledge_id": knowledge.id, "indexed_chunks": count}
    
    return {"document_id": doc.id}

@router.post("/add")
async def add_knowledge(
    title: str = Form(...),
    content: str = Form(...),
    category: str = Form("manual"),
    device_type: str = Form(None),
    user_id: int = Form(None),
    db: Session = Depends(get_db)
):
    knowledge = Knowledge(
        title=title,
        content=content,
        category=category,
        device_type=device_type,
        status="pending",
        creator_id=user_id
    )
    db.add(knowledge)
    db.commit()
    db.refresh(knowledge)
    
    vector_service.add_text(content, {"knowledge_id": knowledge.id})
    
    return {"knowledge_id": knowledge.id}

@router.get("/list")
async def list_knowledge(
    category: str = None,
    device_type: str = None,
    status: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(Knowledge)
    
    if category:
        query = query.filter(Knowledge.category == category)
    if device_type:
        query = query.filter(Knowledge.device_type == device_type)
    if status:
        query = query.filter(Knowledge.status == status)
    
    return {"knowledge_list": query.all()}

@router.get("/{knowledge_id}")
async def get_knowledge(knowledge_id: int, db: Session = Depends(get_db)):
    knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    return knowledge

@router.post("/{knowledge_id}/approve")
async def approve_knowledge(knowledge_id: int, db: Session = Depends(get_db)):
    knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    
    knowledge.status = "approved"
    db.commit()
    
    return {"status": "approved"}

@router.get("/{knowledge_id}/chunks")
async def get_knowledge_chunks(knowledge_id: int, db: Session = Depends(get_db)):
    knowledge = db.query(Knowledge).filter(Knowledge.id == knowledge_id).first()
    if not knowledge:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    
    source = knowledge.source
    if not source:
        return {"chunks": []}
    
    chunks = []
    for i, doc in enumerate(vector_service.documents):
        meta = vector_service.metadata[i]
        if meta.get("source") and source in meta["source"]:
            chunks.append({
                "id": i,
                "content": doc,
                "chunk_number": meta.get("chunk", i)
            })
    
    return {"chunks": chunks, "total": len(chunks)}