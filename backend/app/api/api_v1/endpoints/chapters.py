from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.novel import Chapter
from app.schemas.chapter import ChapterCreate, ChapterResponse, ChapterUpdate
from app.services.chapter_service import get_chapter, get_chapters_by_novel_id, create_chapter, update_chapter, delete_chapter

router = APIRouter()

@router.get("/{chapter_id}", response_model=ChapterResponse)
async def read_chapter(
    chapter_id: int = Path(..., title="章节ID"),
    db: Session = Depends(get_db)
):
    """获取指定ID的章节"""
    chapter = get_chapter(db, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail="章节不存在")
    return chapter

@router.get("/", response_model=List[ChapterResponse])
async def read_chapters(
    novel_id: int = Query(..., title="小说ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取指定小说的所有章节"""
    chapters = get_chapters_by_novel_id(db, novel_id, skip=skip, limit=limit)
    return chapters

@router.post("/", response_model=ChapterResponse)
async def create_novel_chapter(
    chapter_in: ChapterCreate,
    db: Session = Depends(get_db)
):
    """创建新章节"""
    chapter = create_chapter(db, obj_in=chapter_in)
    return chapter

@router.put("/{chapter_id}", response_model=ChapterResponse)
async def update_chapter_api(
    chapter_id: int = Path(..., title="章节ID"),
    chapter_in: ChapterUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """更新章节信息"""
    chapter = get_chapter(db, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail="章节不存在")
    chapter = update_chapter(db, db_obj=chapter, obj_in=chapter_in)
    return chapter

@router.delete("/{chapter_id}")
async def delete_chapter_api(
    chapter_id: int = Path(..., title="章节ID"),
    db: Session = Depends(get_db)
):
    """删除章节"""
    chapter = get_chapter(db, chapter_id)
    if chapter is None:
        raise HTTPException(status_code=404, detail="章节不存在")
    delete_chapter(db, chapter_id)
    return {"success": True} 