from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.character_analysis import CharacterAnalysisResponse, CharacterPersonality, CharacterDetail, NovelCharactersResponse
from app.services.character_analysis_service import analyze_novel_characters, get_character_details, analyze_character_personality, analyze_characters_by_chapter, get_novel_characters_without_analysis

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
    
    返回：
    - 角色列表，包含每个角色出现的章节信息
    """
    try:
        result = await analyze_novel_characters(db, novel_id, force_refresh)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"角色分析失败: {str(e)}")

@router.get("/novels/{novel_id}/characters/analyze-by-chapter", response_model=List[CharacterAnalysisResponse])
async def analyze_characters_by_chapter_range(
    novel_id: int = Path(..., title="小说ID"),
    start_chapter: int = Query(..., title="起始章节ID"),
    end_chapter: int = Query(..., title="结束章节ID"),
    db: Session = Depends(get_db)
):
    """
    分析指定章节范围内的人物角色
    
    - **novel_id**: 小说ID
    - **start_chapter**: 起始章节ID
    - **end_chapter**: 结束章节ID
    
    返回：
    - 角色列表，包含每个角色出现的章节信息
    """
    try:
        result = await analyze_characters_by_chapter(db, novel_id, start_chapter, end_chapter)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"章节角色分析失败: {str(e)}")

@router.get("/novels/{novel_id}/characters", response_model=NovelCharactersResponse)
async def get_novel_characters(
    novel_id: int = Path(..., title="小说ID"),
    db: Session = Depends(get_db)
):
    """
    获取小说中的所有角色，不会自动触发分析
    
    - **novel_id**: 小说ID
    
    返回：
    - 小说ID和角色列表，如果没有角色则返回空列表
    """
    try:
        characters = get_novel_characters_without_analysis(db, novel_id)
        return {
            "novel_id": novel_id,
            "characters": characters
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取角色列表失败: {str(e)}")

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