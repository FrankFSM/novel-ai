from fastapi import APIRouter, Depends, HTTPException, Body, Path, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.models.novel import Character
from app.schemas.character import CharacterCreate, CharacterResponse, CharacterUpdate
from app.services.character_service import get_character, get_characters_by_novel_id, create_character, update_character, delete_character

router = APIRouter()

@router.get("/{character_id}", response_model=CharacterResponse)
async def read_character(
    character_id: int = Path(..., title="角色ID"),
    db: Session = Depends(get_db)
):
    """获取指定ID的角色"""
    character = get_character(db, character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    return character

@router.get("/", response_model=List[CharacterResponse])
async def read_characters(
    novel_id: int = Query(..., title="小说ID"),
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取指定小说的所有角色"""
    characters = get_characters_by_novel_id(db, novel_id, skip=skip, limit=limit)
    return characters

@router.post("/", response_model=CharacterResponse)
async def create_novel_character(
    character_in: CharacterCreate,
    db: Session = Depends(get_db)
):
    """创建新角色"""
    character = create_character(db, obj_in=character_in)
    return character

@router.put("/{character_id}", response_model=CharacterResponse)
async def update_character_api(
    character_id: int = Path(..., title="角色ID"),
    character_in: CharacterUpdate = Body(...),
    db: Session = Depends(get_db)
):
    """更新角色信息"""
    character = get_character(db, character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    character = update_character(db, db_obj=character, obj_in=character_in)
    return character

@router.delete("/{character_id}")
async def delete_character_api(
    character_id: int = Path(..., title="角色ID"),
    db: Session = Depends(get_db)
):
    """删除角色"""
    character = get_character(db, character_id)
    if character is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    delete_character(db, character_id)
    return {"success": True} 