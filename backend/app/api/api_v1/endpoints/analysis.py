from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
import logging
from typing import Dict, Any, Optional

from app.core.database import get_db
from app.models import schemas
from app.services import analysis_service, novel_service
from app.core.openai_client import OpenAIClient
from app.core.config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/relationship-graph", response_model=schemas.RelationshipGraphResponse)
async def get_relationship_graph(
    data: schemas.RelationshipGraphRequest,
    db: Session = Depends(get_db)
):
    """获取关系网络图"""
    # 记录请求参数，包括类型信息
    logger.info(f"关系网络图API请求: novel_id={data.novel_id}, character_id={data.character_id}, depth={data.depth}, force_refresh={data.force_refresh} (类型: {type(data.force_refresh).__name__})")
    
    # 确保force_refresh是布尔值
    force_refresh = bool(data.force_refresh)
    logger.info(f"处理后的force_refresh={force_refresh}")
    
    # 检查小说是否存在
    novel = novel_service.get_novel(db=db, novel_id=data.novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 如果指定了角色ID，检查角色是否存在
    if data.character_id:
        character = novel_service.get_character(db=db, character_id=data.character_id)
        if not character:
            raise HTTPException(status_code=404, detail="角色不存在")
    
    # 调用分析服务获取关系网络图
    try:
        result = await analysis_service.get_relationship_graph(
            db=db, 
            novel_id=data.novel_id,
            character_id=data.character_id,
            depth=data.depth,
            force_refresh=force_refresh  # 使用处理后的值
        )
        return result
    except Exception as e:
        logger.error(f"获取关系网络图失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取关系网络图失败: {str(e)}")

@router.post("/timeline", response_model=schemas.TimelineResponse)
async def get_timeline(
    data: schemas.TimelineRequest,
    db: Session = Depends(get_db)
):
    """获取时间线"""
    # 检查小说是否存在
    novel = novel_service.get_novel(db=db, novel_id=data.novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 如果指定了角色，检查角色是否存在
    if data.character_id:
        character = novel_service.get_character(db=db, character_id=data.character_id)
        if not character:
            raise HTTPException(status_code=404, detail="角色不存在")
    
    try:
        # 获取时间线数据
        timeline_data = analysis_service.get_timeline(
            db=db,
            novel_id=data.novel_id,
            character_id=data.character_id,
            start_chapter=data.start_chapter,
            end_chapter=data.end_chapter
        )
        return timeline_data
    except Exception as e:
        logger.error(f"获取时间线失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取时间线失败: {str(e)}")

@router.get("/character-journey/{novel_id}/{character_id}", response_model=dict)
async def get_character_journey(
    novel_id: int,
    character_id: int,
    db: Session = Depends(get_db)
):
    """获取角色旅程"""
    # 检查小说是否存在
    novel = novel_service.get_novel(db=db, novel_id=novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 检查角色是否存在
    character = novel_service.get_character(db=db, character_id=character_id)
    if not character:
        raise HTTPException(status_code=404, detail="角色不存在")
    
    try:
        # 获取角色旅程数据
        journey_data = analysis_service.get_character_journey(
            db=db,
            novel_id=novel_id,
            character_id=character_id
        )
        return journey_data
    except Exception as e:
        logger.error(f"获取角色旅程失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取角色旅程失败: {str(e)}")

@router.get("/item-lineage/{novel_id}/{item_id}", response_model=dict)
async def get_item_lineage(
    novel_id: int,
    item_id: int,
    db: Session = Depends(get_db)
):
    """获取物品传承历史"""
    # 检查小说是否存在
    novel = novel_service.get_novel(db=db, novel_id=novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 检查物品是否存在
    item = novel_service.get_item(db=db, item_id=item_id)
    if not item:
        raise HTTPException(status_code=404, detail="物品不存在")
    
    try:
        # 获取物品传承数据
        lineage_data = analysis_service.get_item_lineage(
            db=db,
            novel_id=novel_id,
            item_id=item_id
        )
        return lineage_data
    except Exception as e:
        logger.error(f"获取物品传承历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取物品传承历史失败: {str(e)}")

@router.get("/location-events/{novel_id}/{location_id}", response_model=dict)
async def get_location_events(
    novel_id: int,
    location_id: int,
    db: Session = Depends(get_db)
):
    """获取地点相关事件"""
    # 检查小说是否存在
    novel = novel_service.get_novel(db=db, novel_id=novel_id)
    if not novel:
        raise HTTPException(status_code=404, detail="小说不存在")
    
    # 检查地点是否存在
    location = novel_service.get_location(db=db, location_id=location_id)
    if not location:
        raise HTTPException(status_code=404, detail="地点不存在")
    
    try:
        # 获取地点事件数据
        events_data = analysis_service.get_location_events(
            db=db,
            novel_id=novel_id,
            location_id=location_id
        )
        return events_data
    except Exception as e:
        logger.error(f"获取地点事件失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取地点事件失败: {str(e)}")

@router.get("/api-status", response_model=Dict[str, Any])
async def check_api_status():
    """检查OpenAI API的连接状态"""
    results = OpenAIClient.check_api_connectivity()
    return results 