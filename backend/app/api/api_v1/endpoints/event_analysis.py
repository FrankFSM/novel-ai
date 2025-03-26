from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.services.event_analysis_service import get_novel_events, get_event_details, analyze_event_significance

router = APIRouter()

@router.get("/novels/{novel_id}/events", response_model=Dict[str, Any])
async def get_events(
    novel_id: int = Path(..., title="小说ID"),
    force_refresh: bool = Query(False, title="强制刷新"),
    db: Session = Depends(get_db)
):
    """
    获取小说中的所有事件
    
    - **novel_id**: 小说ID
    - **force_refresh**: 是否强制刷新分析结果
    """
    try:
        result = await get_novel_events(db, novel_id, force_refresh)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取事件列表失败: {str(e)}")

@router.get("/events/{event_id}/details", response_model=Dict[str, Any])
async def get_event_detail(
    event_id: int = Path(..., title="事件ID"),
    db: Session = Depends(get_db)
):
    """
    获取事件详细信息
    
    - **event_id**: 事件ID
    """
    try:
        result = await get_event_details(db, event_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取事件详情失败: {str(e)}")

@router.get("/events/{event_id}/significance", response_model=Dict[str, Any])
async def get_event_significance(
    event_id: int = Path(..., title="事件ID"),
    db: Session = Depends(get_db)
):
    """
    分析事件重要性
    
    - **event_id**: 事件ID
    """
    try:
        result = await analyze_event_significance(db, event_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"事件重要性分析失败: {str(e)}")

@router.get("/events/filter", response_model=List[Dict[str, Any]])
async def filter_events(
    novel_id: int = Query(..., title="小说ID"),
    character_id: int = Query(None, title="角色ID"),
    location_id: int = Query(None, title="地点ID"),
    min_importance: int = Query(None, title="最小重要性", ge=1, le=5),
    db: Session = Depends(get_db)
):
    """
    筛选事件
    
    - **novel_id**: 小说ID
    - **character_id**: 角色ID（可选）
    - **location_id**: 地点ID（可选）
    - **min_importance**: 最小重要性评分（可选，范围1-5）
    """
    try:
        # 获取所有事件
        result = await get_novel_events(db, novel_id, False)
        events = result["events"]
        
        # 根据参数筛选
        filtered_events = events
        
        # 按角色筛选
        if character_id:
            filtered_events = [
                event for event in filtered_events
                if any(participant["id"] == character_id for participant in event["participants"])
            ]
        
        # 按地点筛选
        if location_id:
            filtered_events = [
                event for event in filtered_events
                if event["location"] and event["location"]["id"] == location_id
            ]
        
        # 按重要性筛选
        if min_importance:
            filtered_events = [
                event for event in filtered_events
                if event["importance"] and event["importance"] >= min_importance
            ]
        
        return filtered_events
        
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"筛选事件失败: {str(e)}") 