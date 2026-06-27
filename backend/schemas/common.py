"""
通用 schemas
"""
from pydantic import BaseModel
from typing import Optional


class APIResponse(BaseModel):
    code: int = 200
    message: str = "success"
    data: Optional[dict] = None


class ReprocessRequest(BaseModel):
    pdf_path: Optional[str] = None
