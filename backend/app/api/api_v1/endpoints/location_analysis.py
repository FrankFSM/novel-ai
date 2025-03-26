from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.schemas.location_analysis import LocationAnalysisResponse, LocationSignificance, LocationDetail, NovelLocationsResponse
from app.models.schemas import TimelineResponse
from app.services.location_analysis_service import analyze_novel_locations, get_location_details, analyze_location_significance, analyze_all_location_events
from app.services import analysis_service

router = APIRouter()

@router.get("/novels/{novel_id}/locations/analyze", response_model=List[LocationAnalysisResponse])
async def analyze_locations(
    novel_id: int = Path(..., title="小说ID"),
    force_refresh: bool = Query(False, title="强制刷新"),
    db: Session = Depends(get_db)
):
    """
    分析小说中的地点
    
    - **novel_id**: 小说ID
    - **force_refresh**: 是否强制刷新分析结果
    """
    try:
        result = await analyze_novel_locations(db, novel_id, force_refresh)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"地点分析失败: {str(e)}")

@router.get("/locations/{location_id}/details", response_model=LocationDetail)
async def get_location_detail(
    location_id: int = Path(..., title="地点ID"),
    db: Session = Depends(get_db)
):
    """
    获取地点详细信息
    
    - **location_id**: 地点ID
    """
    try:
        result = await get_location_details(db, location_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取地点详情失败: {str(e)}")

@router.get("/locations/{location_id}/significance", response_model=LocationSignificance)
async def get_location_significance(
    location_id: int = Path(..., title="地点ID"),
    db: Session = Depends(get_db)
):
    """
    分析地点重要性
    
    - **location_id**: 地点ID
    """
    try:
        result = await analyze_location_significance(db, location_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"地点重要性分析失败: {str(e)}")

@router.get("/novels/{novel_id}/locations", response_model=NovelLocationsResponse)
async def get_novel_locations(
    novel_id: int = Path(..., title="小说ID"),
    db: Session = Depends(get_db)
):
    """
    获取小说中的所有地点
    
    - **novel_id**: 小说ID
    """
    try:
        locations = await analyze_novel_locations(db, novel_id, force_refresh=False)
        return {
            "novel_id": novel_id,
            "locations": locations
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取地点列表失败: {str(e)}")

@router.get("/locations/{location_id}/timeline", response_model=TimelineResponse)
async def get_location_timeline(
    location_id: int = Path(..., title="地点ID"),
    novel_id: int = Query(..., title="小说ID"),
    start_chapter: int = Query(None, title="开始章节"),
    end_chapter: int = Query(None, title="结束章节"),
    db: Session = Depends(get_db)
):
    """
    获取地点的时间线
    
    - **location_id**: 地点ID
    - **novel_id**: 小说ID
    - **start_chapter**: 开始章节（可选）
    - **end_chapter**: 结束章节（可选）
    """
    try:
        result = analysis_service.get_location_timeline(
            db=db,
            novel_id=novel_id,
            location_id=location_id,
            start_chapter=start_chapter,
            end_chapter=end_chapter
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取地点时间线失败: {str(e)}")

@router.post("/novels/{novel_id}/locations/events/analyze", response_model=Dict[str, Any])
async def analyze_all_location_events_endpoint(
    novel_id: int = Path(..., title="小说ID"),
    force_refresh: bool = Query(False, title="强制刷新"),
    db: Session = Depends(get_db)
):
    """
    分析小说中所有地点的相关事件
    
    - **novel_id**: 小说ID
    - **force_refresh**: 是否强制刷新分析结果
    """
    try:
        result = await analyze_all_location_events(
            db=db, 
            novel_id=novel_id, 
            force_refresh=force_refresh
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"地点事件全局分析失败: {str(e)}") 