"""
搜索相关 schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Any


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, description="查询文本")
    k: int = Field(10, ge=1, le=50, description="返回数量")
    include_images: bool = Field(True, description="是否包含图片结果")


class SearchResultItem(BaseModel):
    id: Optional[str] = None
    type: str = "text"
    title: Optional[str] = ""
    content: str = ""
    description: Optional[str] = None
    similarity: int = 0
    source_type: Optional[str] = None
    source_file: Optional[str] = None
    page: Optional[int] = None
    tags: List[str] = []
    image_url: Optional[str] = None
    image_filename: Optional[str] = None
    image_ids: List[str] = []
    related_images: List[Any] = []


class SearchResponse(BaseModel):
    query: str
    results: List[SearchResultItem]
    total: int


class SearchStatsResponse(BaseModel):
    total_chunks: int
    text_chunks: int
    image_chunks: int
