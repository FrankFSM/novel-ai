from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field

class CharacterTrait(BaseModel):
    """角色特质模型"""
    trait: str
    description: str
    evidence: Optional[str] = None

class CharacterPersonalityTrait(BaseModel):
    """性格特征项"""
    trait: str
    description: str
    score: int = Field(..., ge=1, le=10)

class CharacterPersonality(BaseModel):
    """角色性格分析"""
    id: int
    name: str
    mbti: Optional[str] = None
    personality_summary: str
    traits: List[CharacterPersonalityTrait] = []
    strengths: List[str] = []
    weaknesses: List[str] = []

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

class CharacterDetailSection(BaseModel):
    """角色详情部分"""
    title: str
    content: str

class CharacterDetail(BaseModel):
    """角色详细信息"""
    id: int
    name: str
    alias: Optional[List[str]] = []
    description: Optional[str] = None
    first_appearance: Optional[int] = None
    importance: Optional[int] = 1
    sections: List[CharacterDetailSection] = []

class ChapterAppearance(BaseModel):
    """角色在章节中的出现信息"""
    chapter_id: int
    chapter_title: str
    chapter_number: int
    description: Optional[str] = None  # 添加章节特定的角色描述

class CharacterAnalysisResponse(BaseModel):
    """角色分析响应模型"""
    id: int
    name: str
    alias: Optional[List[str]] = None
    description: Optional[str] = None
    first_appearance: Optional[int] = None
    importance: Optional[int] = None
    chapters: Optional[List[int]] = None  # 角色出现的章节ID列表
    chapter_info: Optional[List[ChapterAppearance]] = None  # 角色出现的章节详细信息

class NovelCharactersResponse(BaseModel):
    """小说角色列表响应模型"""
    novel_id: int
    characters: List[CharacterAnalysisResponse]

class CharacterAnalysisRequest(BaseModel):
    """角色分析请求模型"""
    character_id: int
    novel_id: int
    analysis_type: str
    analysis_data: Optional[Dict[str, Any]] = None

class CharacterAnalysisResult(BaseModel):
    """角色分析结果模型"""
    id: int
    name: str
    analysis_type: str
    analysis_result: str
    analysis_date: str
    analysis_data: Optional[Dict[str, Any]] = None

class CharacterAnalysisHistory(BaseModel):
    """角色分析历史模型"""
    id: int
    character_id: int
    novel_id: int
    analysis_type: str
    analysis_date: str
    analysis_result: str
    analysis_data: Optional[Dict[str, Any]] = None

class CharacterAnalysisHistoryResponse(BaseModel):
    """角色分析历史响应模型"""
    id: int
    character_id: int
    novel_id: int
    analysis_type: str
    analysis_date: str
    analysis_result: str
    analysis_data: Optional[Dict[str, Any]] = None

class CharacterAnalysisHistoryListResponse(BaseModel):
    """角色分析历史列表响应模型"""
    id: int
    character_id: int
    novel_id: int
    analysis_type: str
    analysis_date: str
    analysis_result: str
    analysis_data: Optional[Dict[str, Any]] = None

class CharacterAnalysisHistoryDeleteRequest(BaseModel):
    """角色分析历史删除请求模型"""
    id: int

class CharacterAnalysisHistoryDeleteResponse(BaseModel):
    """角色分析历史删除响应模型"""
    id: int
    message: str 