"""
作业指引相关 schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class GuideCreateRequest(BaseModel):
    device_type: str = Field(..., min_length=1, description="设备类型")
    fault_type: str = Field(..., min_length=1, description="故障类型")
    user_id: Optional[int] = None


class GuideStep(BaseModel):
    step: int
    content: str


class GuideCreateResponse(BaseModel):
    task_id: int
    steps: List[GuideStep]
    summary: Optional[str] = None


class CheckpointCreate(BaseModel):
    step_number: int
    checkpoint_type: str
    actual_value: str


class TaskOut(BaseModel):
    id: int
    title: str
    device_type: Optional[str] = None
    status: str
    current_step: int = 0

    class Config:
        from_attributes = True


class GuideDetailResponse(BaseModel):
    task: TaskOut
    steps: List[GuideStep]
