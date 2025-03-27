from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime

# 基础模型
class BaseSchema(BaseModel):
    class Config:
        orm_mode = True

# 小说相关模型
class NovelBase(BaseSchema):
    title: str
    author: str
    description: Optional[str] = None
    cover_url: Optional[str] = None

class NovelCreate(NovelBase):
    pass

class NovelResponse(NovelBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

class NovelDetail(NovelResponse):
    chapters_count: int
    characters_count: int
    
# 章节相关模型
class ChapterBase(BaseSchema):
    title: str
    content: str
    number: int

class ChapterCreate(ChapterBase):
    pass

class ChapterResponse(ChapterBase):
    id: int
    novel_id: int
    word_count: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# 角色相关模型
class CharacterBase(BaseSchema):
    name: str
    alias: Optional[List[str]] = None
    description: Optional[str] = None

class CharacterCreate(CharacterBase):
    novel_id: int
    first_appearance: Optional[int] = None

class CharacterResponse(CharacterBase):
    id: int
    novel_id: int

class CharacterDetail(CharacterResponse):
    first_appearance: Optional[int] = None
    relationships: Optional[List["RelationshipResponse"]] = None
    owned_items: Optional[List["ItemResponse"]] = None
    
# 地点相关模型
class LocationBase(BaseSchema):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class LocationCreate(LocationBase):
    novel_id: int

class LocationResponse(LocationBase):
    id: int
    novel_id: int

# 物品相关模型
class ItemBase(BaseSchema):
    name: str
    description: Optional[str] = None
    owner_id: Optional[int] = None

class ItemCreate(ItemBase):
    novel_id: int

class ItemResponse(ItemBase):
    id: int
    novel_id: int

# 事件相关模型
class EventBase(BaseSchema):
    name: str
    description: Optional[str] = None
    chapter_id: Optional[int] = None
    location_id: Optional[int] = None
    time_description: Optional[str] = None
    importance: Optional[int] = 1

class EventCreate(EventBase):
    novel_id: int
    participants: Optional[List[Dict[str, Any]]] = None

class EventResponse(EventBase):
    id: int
    novel_id: int

class EventDetail(EventResponse):
    participants: List[Dict[str, Any]] = []
    location: Optional[Dict[str, Any]] = None

# 关系相关模型
class RelationshipBase(BaseSchema):
    from_character_id: int
    to_character_id: int
    relation_type: str
    description: Optional[str] = None
    first_chapter_id: Optional[int] = None

class RelationshipCreate(RelationshipBase):
    novel_id: int

class RelationshipResponse(RelationshipBase):
    id: int
    novel_id: int

# 文本块相关模型
class TextChunkBase(BaseSchema):
    content: str
    start_char: int
    end_char: int

class TextChunkCreate(TextChunkBase):
    chapter_id: int

class TextChunkResponse(TextChunkBase):
    id: int
    chapter_id: int
    vector_id: Optional[str] = None

# 智能问答相关模型
class QuestionRequest(BaseModel):
    novel_id: int
    question: str
    use_rag: bool = True  # 是否使用检索增强生成

class AnswerResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []  # 来源引用
    confidence: float

# 分析相关模型
class RelationshipGraphRequest(BaseModel):
    novel_id: int
    character_id: Optional[int] = None  # 如果指定，则只返回与该角色相关的关系
    depth: int = 1  # 关系图深度
    force_refresh: bool = False  # 是否强制刷新缓存

class RelationshipGraphResponse(BaseModel):
    nodes: List[Dict[str, Any]]
    edges: List[Dict[str, Any]]

class TimelineRequest(BaseModel):
    novel_id: int
    character_id: Optional[int] = None  # 如果指定，则只返回该角色相关的事件
    start_chapter: Optional[int] = None
    end_chapter: Optional[int] = None

class TimelineResponse(BaseModel):
    events: List[EventDetail]

# 文件上传相关模型
class UploadNovelRequest(BaseModel):
    title: str
    author: str
    description: Optional[str] = None

class UploadNovelResponse(BaseModel):
    novel_id: int
    message: str

# 实体提取相关模型
class EntityExtractionRequest(BaseModel):
    text: str
    novel_id: Optional[int] = None

class EntityExtractionResponse(BaseModel):
    persons: List[Dict[str, Any]] = []
    locations: List[Dict[str, Any]] = []
    items: List[Dict[str, Any]] = []
    events: List[Dict[str, Any]] = []
    times: List[Dict[str, Any]] = []

# 用户相关模型
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenPayload(BaseModel):
    sub: Optional[str] = None

class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_superuser: bool 