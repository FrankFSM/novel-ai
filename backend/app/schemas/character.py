from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class CharacterBase(BaseModel):
    """角色基础模型"""
    name: str
    novel_id: int
    description: Optional[str] = None
    importance: Optional[int] = None
    image_url: Optional[str] = None

class CharacterCreate(CharacterBase):
    """创建角色模型"""
    pass

class CharacterUpdate(BaseModel):
    """更新角色模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    importance: Optional[int] = None
    image_url: Optional[str] = None

class CharacterResponse(CharacterBase):
    """角色响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class CharacterRelationshipBase(BaseModel):
    """角色关系基础模型"""
    source_character_id: int
    target_character_id: int
    relationship_type: str
    description: Optional[str] = None
    importance: Optional[int] = None

class CharacterRelationshipCreate(CharacterRelationshipBase):
    """创建角色关系模型"""
    pass

class CharacterRelationshipUpdate(BaseModel):
    """更新角色关系模型"""
    relationship_type: Optional[str] = None
    description: Optional[str] = None
    importance: Optional[int] = None

class CharacterRelationshipResponse(CharacterRelationshipBase):
    """角色关系响应模型"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True 