from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from fastapi import UploadFile

from app.models import novel, schemas
from app.core.openai_client import OpenAIClient

logger = logging.getLogger(__name__)

def get_novel(db: Session, novel_id: int) -> Optional[novel.Novel]:
    """获取小说详情"""
    return db.query(novel.Novel).filter(novel.Novel.id == novel_id).first()

def get_novels(db: Session, skip: int = 0, limit: int = 100) -> List[novel.Novel]:
    """获取小说列表"""
    return db.query(novel.Novel).offset(skip).limit(limit).all()

def create_novel(db: Session, novel_data: schemas.NovelCreate) -> novel.Novel:
    """创建新小说"""
    db_novel = novel.Novel(
        title=novel_data.title,
        author=novel_data.author,
        description=novel_data.description,
        cover_url=novel_data.cover_url
    )
    db.add(db_novel)
    db.commit()
    db.refresh(db_novel)
    return db_novel

def update_novel(db: Session, novel_id: int, novel_data: schemas.NovelCreate) -> novel.Novel:
    """更新小说信息"""
    db_novel = get_novel(db, novel_id)
    db_novel.title = novel_data.title
    db_novel.author = novel_data.author
    db_novel.description = novel_data.description
    db_novel.cover_url = novel_data.cover_url
    db.commit()
    db.refresh(db_novel)
    return db_novel

def delete_novel(db: Session, novel_id: int) -> None:
    """删除小说"""
    db_novel = get_novel(db, novel_id)
    db.delete(db_novel)
    db.commit()

async def process_novel_file(db: Session, novel_id: int, file: UploadFile) -> None:
    """处理上传的小说文件（示例实现）"""
    try:
        # 读取文件内容
        content = await file.read()
        text = content.decode('utf-8')
        
        # 简单地按行分割文本作为示例
        lines = text.split('\n')
        chapters = []
        current_chapter = {"title": "", "content": []}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 非常简单的章节检测（实际应用中需要更复杂的逻辑）
            if line.startswith('第') and ('章' in line or '节' in line):
                # 保存之前的章节
                if current_chapter["title"] and current_chapter["content"]:
                    chapters.append(current_chapter)
                # 开始新章节
                current_chapter = {"title": line, "content": []}
            else:
                current_chapter["content"].append(line)
        
        # 不要忘记最后一章
        if current_chapter["title"] and current_chapter["content"]:
            chapters.append(current_chapter)
        
        # 保存章节到数据库
        for i, chapter_data in enumerate(chapters):
            chapter = novel.Chapter(
                title=chapter_data["title"],
                content="\n".join(chapter_data["content"]),
                number=i+1,
                word_count=len("".join(chapter_data["content"]))
            )
            db.add(chapter)
            db.flush()  # 获取ID
            
            # 建立小说与章节的关联
            db_novel = get_novel(db, novel_id)
            db_novel.chapters.append(chapter)
        
        db.commit()
        logger.info(f"成功处理小说文件，共导入{len(chapters)}章节")
        
    except Exception as e:
        db.rollback()
        logger.error(f"处理小说文件失败: {str(e)}")
        raise

def get_novel_statistics(db: Session, novel_id: int) -> Dict[str, Any]:
    """获取小说统计信息"""
    db_novel = get_novel(db, novel_id)
    
    # 计算总字数
    total_words = 0
    for chapter in db_novel.chapters:
        total_words += chapter.word_count or 0
    
    # 统计人物、地点、物品数量
    character_count = len(db_novel.characters)
    location_count = len(db_novel.locations)
    item_count = len(db_novel.items)
    
    return {
        "total_chapters": len(db_novel.chapters),
        "total_words": total_words,
        "character_count": character_count,
        "location_count": location_count,
        "item_count": item_count
    }

async def extract_novel_entities(db: Session, novel_id: int) -> None:
    """提取小说实体（示例实现）"""
    try:
        db_novel = get_novel(db, novel_id)
        
        # 处理每个章节
        for chapter in db_novel.chapters:
            # 示例：每1000字为一个块
            content = chapter.content
            chunk_size = 1000
            
            for i in range(0, len(content), chunk_size):
                chunk_text = content[i:i+chunk_size]
                
                # 创建文本块
                text_chunk = novel.TextChunk(
                    chapter_id=chapter.id,
                    content=chunk_text,
                    start_char=i,
                    end_char=i+len(chunk_text)
                )
                db.add(text_chunk)
                db.flush()
                
                # 使用OpenAI API提取实体
                entities = await OpenAIClient.extract_entities(chunk_text)
                
                # 处理人物
                for person_data in entities.get('persons', []):
                    # 查找或创建人物
                    character = db.query(novel.Character).filter(
                        novel.Character.novel_id == novel_id,
                        novel.Character.name == person_data['name']
                    ).first()
                    
                    if not character:
                        character = novel.Character(
                            novel_id=novel_id,
                            name=person_data['name'],
                            alias=person_data.get('alias', []),
                            description=person_data.get('description', ""),
                            first_appearance=chapter.id
                        )
                        db.add(character)
                        db.flush()
                
                # 处理地点和物品等其他实体...
                
        db.commit()
        logger.info(f"成功提取小说实体")
        
    except Exception as e:
        db.rollback()
        logger.error(f"提取小说实体失败: {str(e)}")
        raise

def get_character(db: Session, character_id: int) -> Optional[novel.Character]:
    """获取角色详情"""
    return db.query(novel.Character).filter(novel.Character.id == character_id).first()

def get_location(db: Session, location_id: int) -> Optional[novel.Location]:
    """获取地点详情"""
    return db.query(novel.Location).filter(novel.Location.id == location_id).first()

def get_item(db: Session, item_id: int) -> Optional[novel.Item]:
    """获取物品详情"""
    return db.query(novel.Item).filter(novel.Item.id == item_id).first() 