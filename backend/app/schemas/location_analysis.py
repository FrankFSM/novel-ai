from typing import Optional, List, Dict, Any
from pydantic import BaseModel

class LocationFeature(BaseModel):
    """地点特征模型"""
    feature: str
    description: str
    evidence: Optional[str] = None

class LocationSignificance(BaseModel):
    """地点重要性分析模型"""
    name: str
    significance: List[str]
    features: List[LocationFeature]
    description: Optional[str] = None
    analysis: Optional[str] = None

class RelatedLocation(BaseModel):
    """相关地点简略信息"""
    id: int
    name: str
    description: Optional[str] = None

class RelatedCharacter(BaseModel):
    """相关角色简略信息"""
    id: int
    name: str
    importance: Optional[int] = None

class RelatedEvent(BaseModel):
    """相关事件简略信息"""
    id: int
    name: str
    description: Optional[str] = None
    chapter_id: Optional[int] = None
    importance: Optional[int] = None
    time_description: Optional[str] = None

class LocationDetail(BaseModel):
    """地点详细信息"""
    id: int
    name: str
    description: Optional[str] = None
    parent: Optional[RelatedLocation] = None
    sub_locations: List[RelatedLocation]
    events: List[RelatedEvent]
    characters: List[RelatedCharacter]

class LocationAnalysisResponse(BaseModel):
    """地点分析结果响应"""
    id: int
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None
    events_count: Optional[int] = 0

class NovelLocationsResponse(BaseModel):
    """小说地点列表响应"""
    novel_id: int
    locations: List[LocationAnalysisResponse] 