from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session

from app.models.novel import Character
from app.schemas.character import CharacterCreate, CharacterUpdate

def get_character(db: Session, character_id: int) -> Optional[Character]:
    """根据ID获取角色"""
    return db.query(Character).filter(Character.id == character_id).first()

def get_characters_by_novel_id(db: Session, novel_id: int, skip: int = 0, limit: int = 100) -> List[Character]:
    """获取指定小说的所有角色"""
    return db.query(Character).filter(Character.novel_id == novel_id).offset(skip).limit(limit).all()

def create_character(db: Session, obj_in: CharacterCreate) -> Character:
    """创建新角色"""
    db_obj = Character(
        novel_id=obj_in.novel_id,
        name=obj_in.name,
        description=obj_in.description,
        importance=obj_in.importance,
        image_url=obj_in.image_url
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_character(db: Session, db_obj: Character, obj_in: Union[CharacterUpdate, Dict[str, Any]]) -> Character:
    """更新角色信息"""
    if isinstance(obj_in, dict):
        update_data = obj_in
    else:
        update_data = obj_in.dict(exclude_unset=True)
    
    for field in update_data:
        setattr(db_obj, field, update_data[field])
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def delete_character(db: Session, character_id: int) -> None:
    """删除角色"""
    character = db.query(Character).filter(Character.id == character_id).first()
    db.delete(character)
    db.commit() 