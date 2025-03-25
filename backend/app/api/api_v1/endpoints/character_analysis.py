from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.character_analysis import CharacterAnalysisResponse, CharacterPersonality, CharacterDetail, NovelCharactersResponse
from app.services.character_analysis_service import analyze_novel_characters, get_character_details, analyze_character_personality

router = APIRouter()

@router.get("/novels/{novel_id}/characters/analyze", response_model=List[CharacterAnalysisResponse])
async def analyze_characters(
    novel_id: int = Path(..., title="小说ID"),
    force_refresh: bool = Query(False, title="强制刷新"),
    db: Session = Depends(get_db)
):
    """
    分析小说中的人物角色
    
    - **novel_id**: 小说ID
    - **force_refresh**: 是否强制刷新分析结果
    """
    try:
        result = await analyze_novel_characters(db, novel_id, force_refresh)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"角色分析失败: {str(e)}")

@router.get("/characters/{character_id}/details", response_model=CharacterDetail)
async def get_character_detail(
    character_id: int = Path(..., title="角色ID"),
    db: Session = Depends(get_db)
):
    """
    获取角色详细信息
    
    - **character_id**: 角色ID
    """
    try:
        result = await get_character_details(db, character_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取角色详情失败: {str(e)}")

@router.get("/characters/{character_id}/personality", response_model=CharacterPersonality)
async def get_character_personality(
    character_id: int = Path(..., title="角色ID"),
    db: Session = Depends(get_db)
):
    """
    分析角色性格
    
    - **character_id**: 角色ID
    """
    try:
        result = await analyze_character_personality(db, character_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"角色性格分析失败: {str(e)}") 