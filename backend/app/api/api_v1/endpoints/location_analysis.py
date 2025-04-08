from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.core.database import get_db
from app.schemas.location_analysis import LocationAnalysisResponse, LocationSignificance, LocationDetail, NovelLocationsResponse
from app.models.schemas import TimelineResponse
from app.services.location_analysis_service import analyze_novel_locations, get_location_details, analyze_location_significance, analyze_all_location_events, analyze_single_chapter, analyze_locations_by_chapter
from app.services import analysis_service
from app.models.novel import Location, Event

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

@router.get("/novels/{novel_id}/chapters/{chapter_id}/analyze", response_model=List[LocationAnalysisResponse])
async def analyze_chapter_locations(
    novel_id: int = Path(..., title="小说ID"),
    chapter_id: int = Path(..., title="章节ID"),
    db: Session = Depends(get_db)
):
    """
    分析单个章节的地点
    
    - **novel_id**: 小说ID
    - **chapter_id**: 章节ID
    
    返回：
    - 章节中的地点列表
    """
    try:
        result = await analyze_single_chapter(db, novel_id, chapter_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"章节地点分析失败: {str(e)}")

@router.get("/novels/{novel_id}/chapters/{chapter_id}/locations", response_model=List[LocationAnalysisResponse])
async def get_chapter_locations(
    novel_id: int = Path(..., title="小说ID"),
    chapter_id: int = Path(..., title="章节ID"),
    db: Session = Depends(get_db)
):
    """
    获取特定章节的已有地点数据(不触发分析)
    
    - **novel_id**: 小说ID
    - **chapter_id**: 章节ID
    
    返回：
    - 该章节已有的地点列表
    """
    try:
        # 查询数据库中已有的章节地点数据
        locations = db.query(Location).filter(
            Location.novel_id == novel_id,
            Location.chapter_id == chapter_id
        ).all()
        
        # 转换为响应格式
        result = []
        for loc in locations:
            # 计算相关事件数量
            events_count = db.query(Event).filter(
                Event.location_id == loc.id
            ).count()
            
            # 构建响应对象
            location_data = {
                "id": loc.id,
                "name": loc.name,
                "description": loc.description,
                "parent_id": loc.parent_id,
                "events_count": events_count
            }
            result.append(location_data)
            
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取章节地点失败: {str(e)}")

@router.get("/novels/{novel_id}/locations/analyze-by-chapter", response_model=List[LocationAnalysisResponse])
async def analyze_locations_by_chapter_range(
    novel_id: int = Path(..., title="小说ID"),
    start_chapter: int = Query(..., title="起始章节ID"),
    end_chapter: int = Query(..., title="结束章节ID"),
    db: Session = Depends(get_db)
):
    """
    分析指定章节范围内的地点
    
    - **novel_id**: 小说ID
    - **start_chapter**: 起始章节ID
    - **end_chapter**: 结束章节ID
    
    返回：
    - 地点列表，包含每个地点的章节信息
    """
    try:
        result = await analyze_locations_by_chapter(db, novel_id, start_chapter, end_chapter)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"章节范围地点分析失败: {str(e)}") 