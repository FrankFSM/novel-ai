from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class CharacterTrait(BaseModel):
    """角色特质模型"""
    trait: str
    description: str
    evidence: Optional[str] = None

class CharacterPersonality(BaseModel):
    """角色性格分析模型"""
    name: str
    personality: List[str]
    traits: List[CharacterTrait]
    description: Optional[str] = None
    analysis: Optional[str] = None
    quotes: Optional[List[str]] = None

class RelatedCharacter(BaseModel):
    """相关角色简略信息"""
    id: int
    name: str

class CharacterRelationship(BaseModel):
    """角色关系信息"""
    id: int
    character: RelatedCharacter
    relation_type: str
    description: Optional[str] = None
    direction: str  # "to" 或 "from"

class CharacterEvent(BaseModel):
    """角色事件信息"""
    id: int
    name: str
    description: Optional[str] = None
    role: Optional[str] = None

class CharacterItem(BaseModel):
    """角色物品信息"""
    id: int
    name: str
    description: Optional[str] = None

class CharacterDetail(BaseModel):
    """角色详细信息"""
    id: int
    name: str
    alias: Optional[List[str]] = None
    description: Optional[str] = None
    first_appearance: Optional[int] = None
    relationships: List[CharacterRelationship]
    events: List[CharacterEvent]
    items: List[CharacterItem]

class CharacterAnalysisResponse(BaseModel):
    """角色分析结果响应"""
    id: int
    name: str
    alias: Optional[List[str]] = None
    description: Optional[str] = None
    first_appearance: Optional[int] = None

class NovelCharactersResponse(BaseModel):
    """小说角色列表响应"""
    novel_id: int
    characters: List[CharacterAnalysisResponse] 