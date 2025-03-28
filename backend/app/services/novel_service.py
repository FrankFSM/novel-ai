from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import logging
from fastapi import UploadFile
import re

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
    """处理上传的小说文件"""
    try:
        # 读取文件内容
        content = await file.read()
        text = content.decode('utf-8')
        
        # 简单的章节分割（按"第X章"分割）
        chapters = re.split(r'第[一二三四五六七八九十百千万\d]+章', text)
        
        if len(chapters) <= 1:
            # 如果没有找到章节标记，将整个内容作为一个章节
            chapters = [text]
        
        # 删除空白章节
        chapters = [ch.strip() for ch in chapters if ch.strip()]
        
        # 保存章节
        for i, chapter_content in enumerate(chapters, 1):
            chapter = novel.Chapter(
                novel_id=novel_id,
                title=f"第{i}章",
                content=chapter_content,
                number=i,
                word_count=len(chapter_content)
            )
            db.add(chapter)
        
        db.commit()
        
    except Exception as e:
        logger.error(f"处理小说文件失败: {str(e)}")
        db.rollback()
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

def get_novel_chapters_content(db: Session, novel_id: int, limit: Optional[int] = None) -> str:
    """获取小说章节内容
    
    Args:
        db: 数据库会话
        novel_id: 小说ID
        limit: 限制返回的章节数量，如果为None则返回所有章节
        
    Returns:
        合并后的章节内容
    """
    # 获取小说
    db_novel = get_novel(db, novel_id)
    if not db_novel:
        return ""
        
    # 查询章节，按章节序号排序
    chapters = db.query(novel.Chapter).filter(
        novel.Chapter.novel_id == novel_id
    ).order_by(novel.Chapter.number)
    
    if limit:
        chapters = chapters.limit(limit)
    
    chapters = chapters.all()
    
    if not chapters:
        return ""
    
    # 合并章节内容
    content_parts = []
    for chapter in chapters:
        content_parts.append(f"第{chapter.number}章 {chapter.title}\n\n")
        content_parts.append(chapter.content)
        content_parts.append("\n\n")  # 章节之间添加空行分隔
    
    return "".join(content_parts)

def get_chapters_content_by_range(db: Session, novel_id: int, start_chapter_id: int, end_chapter_id: int) -> str:
    """获取指定章节范围的小说内容
    
    Args:
        db: 数据库会话
        novel_id: 小说ID
        start_chapter_id: 起始章节ID
        end_chapter_id: 结束章节ID
        
    Returns:
        合并后的章节内容
    """
    # 获取小说
    db_novel = get_novel(db, novel_id)
    if not db_novel:
        return ""
    
    # 获取起始和结束章节的序号，用于后续查询
    start_chapter = db.query(novel.Chapter).filter(
        novel.Chapter.id == start_chapter_id,
        novel.Chapter.novel_id == novel_id
    ).first()
    
    end_chapter = db.query(novel.Chapter).filter(
        novel.Chapter.id == end_chapter_id,
        novel.Chapter.novel_id == novel_id
    ).first()
    
    if not start_chapter or not end_chapter:
        return ""
    
    # 查询章节范围
    chapters = db.query(novel.Chapter).filter(
        novel.Chapter.novel_id == novel_id,
        novel.Chapter.number >= start_chapter.number,
        novel.Chapter.number <= end_chapter.number
    ).order_by(novel.Chapter.number).all()
    
    if not chapters:
        return ""
    
    # 合并章节内容
    content_parts = []
    for chapter in chapters:
        content_parts.append(f"第{chapter.number}章 {chapter.title}\n\n")
        content_parts.append(chapter.content)
        content_parts.append("\n\n")  # 章节之间添加空行分隔
    
    return "".join(content_parts)

async def process_novel_content(db: Session, novel_id: int, content: str, title_override: Optional[str] = None) -> None:
    """处理小说内容
    
    Args:
        db: 数据库会话
        novel_id: 小说ID
        content: 小说内容
        title_override: 覆盖自动检测的标题（可选）
    """
    try:
        # 使用正则表达式找到所有章节标题和内容
        chapter_pattern = r'(第[一二三四五六七八九十百千万\d]+章[^\n]*)\n(.*?)(?=\n第[一二三四五六七八九十百千万\d]+章|$)'
        chapters = re.findall(chapter_pattern, content, re.DOTALL)
        
        if not chapters:
            # 如果没有找到章节标记，将整个内容作为一个章节
            if title_override:
                # 使用传入的标题
                chapter_title = title_override
            else:
                # 默认标题
                chapter_title = "第1章"
            chapters = [(chapter_title, content.strip())]
        
        # 保存章节
        for i, (title, chapter_content) in enumerate(chapters, 1):
            # 如果只有一个章节且有自定义标题，则使用自定义标题
            actual_title = title_override if (len(chapters) == 1 and title_override) else title.strip()
            
            chapter = novel.Chapter(
                novel_id=novel_id,
                title=actual_title,
                content=chapter_content.strip(),
                number=i,
                word_count=len(chapter_content.strip())
            )
            db.add(chapter)
        
        db.commit()
        logger.info(f"成功处理小说内容，共导入{len(chapters)}章节")
        
    except Exception as e:
        logger.error(f"处理小说内容失败: {str(e)}")
        db.rollback()
        raise

def get_chapter_content(db: Session, chapter_id: int) -> str:
    """获取单个章节的内容
    
    Args:
        db: 数据库会话
        chapter_id: 章节ID
        
    Returns:
        章节内容
    """
    chapter = db.query(novel.Chapter).filter(
        novel.Chapter.id == chapter_id
    ).first()
    
    if not chapter:
        return ""
    
    # 格式化章节内容，确保包含章节标题
    content = f"第{chapter.number}章 {chapter.title}\n\n{chapter.content}"
    return content 