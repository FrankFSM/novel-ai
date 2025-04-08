from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class ChapterBase(BaseModel):
    """章节基础模型"""
    title: str
    content: str
    number: int
    word_count: Optional[int] = None

class ChapterCreate(BaseModel):
    """创建章节模型"""
    title: str
    content: str
    number: int
    novel_id: Optional[int] = None
    word_count: Optional[int] = None

class ChapterUpdate(BaseModel):
    """更新章节模型"""
    title: Optional[str] = None
    content: Optional[str] = None
    number: Optional[int] = None
    word_count: Optional[int] = None

class ChapterResponse(ChapterBase):
    """章节响应模型"""
    id: int
    novel_id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True 