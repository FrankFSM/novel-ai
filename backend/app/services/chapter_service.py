from typing import List, Optional, Dict, Any, Union
from sqlalchemy.orm import Session

from app.models.novel import Chapter
from app.schemas.chapter import ChapterCreate, ChapterUpdate

def get_chapter(db: Session, chapter_id: int) -> Optional[Chapter]:
    """根据ID获取章节"""
    return db.query(Chapter).filter(Chapter.id == chapter_id).first()

def get_chapters_by_novel_id(db: Session, novel_id: int, skip: int = 0, limit: int = 100) -> List[Chapter]:
    """获取指定小说的所有章节"""
    return db.query(Chapter).filter(
        Chapter.novel_id == novel_id
    ).order_by(Chapter.number).offset(skip).limit(limit).all()

def create_chapter(db: Session, obj_in: ChapterCreate) -> Chapter:
    """创建新章节"""
    # 如果没有提供字数，计算内容长度作为字数
    word_count = obj_in.word_count if obj_in.word_count is not None else len(obj_in.content)
    
    db_obj = Chapter(
        novel_id=obj_in.novel_id,
        title=obj_in.title,
        content=obj_in.content,
        number=obj_in.number,
        word_count=word_count
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_chapter(db: Session, db_obj: Chapter, obj_in: Union[ChapterUpdate, Dict[str, Any]]) -> Chapter:
    """更新章节信息"""
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

def delete_chapter(db: Session, chapter_id: int) -> None:
    """删除章节"""
    chapter = get_chapter(db, chapter_id)
    if chapter:
        db.delete(chapter)
        db.commit() 