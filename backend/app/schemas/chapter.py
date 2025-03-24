from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class ChapterBase(BaseModel):
    """章节基础模型"""
    title: str
    content: str
    chapter_number: int
    novel_id: int
    word_count: Optional[int] = None

class ChapterCreate(ChapterBase):
    """创建章节模型"""
    pass

class ChapterUpdate(BaseModel):
    """更新章节模型"""
    title: Optional[str] = None
    content: Optional[str] = None
    chapter_number: Optional[int] = None
    word_count: Optional[int] = None

class ChapterResponse(ChapterBase):
    """章节响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True 