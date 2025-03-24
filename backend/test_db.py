#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path
import logging
from sqlalchemy.orm import Session

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 导入所需模块
from app.core.database import Base, engine, SessionLocal
from app.models.novel import Novel, Chapter, Character, Location, Item, Event, Relationship
from app.services import novel_service, chapter_service

def setup_db():
    """初始化数据库"""
    logger.info("删除旧数据库...")
    if os.path.exists("novel_ai.db"):
        os.remove("novel_ai.db")
    
    logger.info("创建新数据库...")
    Base.metadata.create_all(bind=engine)

def test_novel_creation(db: Session):
    """测试小说创建"""
    logger.info("测试小说创建...")
    
    # 创建小说
    novel = Novel(
        title="测试小说",
        author="测试作者",
        description="这是一个测试小说"
    )
    db.add(novel)
    db.commit()
    db.refresh(novel)
    
    assert novel.id is not None
    logger.info(f"小说创建成功，ID: {novel.id}")
    return novel

def test_chapter_creation(db: Session, novel: Novel):
    """测试章节创建"""
    logger.info("测试章节创建...")
    
    # 创建章节
    chapters = []
    for i in range(1, 4):
        chapter = Chapter(
            novel_id=novel.id,
            title=f"第{i}章",
            content=f"这是第{i}章的内容",
            number=i,
            word_count=100
        )
        chapters.append(chapter)
    
    db.add_all(chapters)
    db.commit()
    
    # 验证章节数量
    db.refresh(novel)
    assert len(novel.chapters) == 3
    logger.info(f"章节创建成功，数量: {len(novel.chapters)}")
    return chapters

def test_character_creation(db: Session, novel: Novel):
    """测试角色创建"""
    logger.info("测试角色创建...")
    
    # 创建角色
    character = Character(
        novel_id=novel.id,
        name="测试角色",
        description="这是一个测试角色"
    )
    db.add(character)
    db.commit()
    db.refresh(character)
    
    assert character.id is not None
    logger.info(f"角色创建成功，ID: {character.id}")
    return character

def test_relationship_creation(db: Session, novel: Novel):
    """测试关系创建"""
    logger.info("测试关系创建...")
    
    # 创建两个角色
    char1 = Character(novel_id=novel.id, name="角色1")
    char2 = Character(novel_id=novel.id, name="角色2")
    db.add_all([char1, char2])
    db.commit()
    
    # 创建关系
    relationship = Relationship(
        novel_id=novel.id,
        from_character_id=char1.id,
        to_character_id=char2.id,
        relation_type="朋友",
        description="他们是好朋友"
    )
    db.add(relationship)
    db.commit()
    
    assert relationship.id is not None
    logger.info(f"关系创建成功，ID: {relationship.id}")
    return relationship

def test_cascade_delete(db: Session, novel: Novel):
    """测试级联删除"""
    logger.info("测试级联删除...")
    
    # 获取删除前的数量
    chapter_count = db.query(Chapter).count()
    character_count = db.query(Character).count()
    relationship_count = db.query(Relationship).count()
    
    # 删除小说
    db.delete(novel)
    db.commit()
    
    # 验证相关数据都被删除
    assert db.query(Chapter).count() == 0
    assert db.query(Character).count() == 0
    assert db.query(Relationship).count() == 0
    
    logger.info(f"级联删除成功，删除了 {chapter_count} 个章节，{character_count} 个角色，{relationship_count} 个关系")

def main():
    """主测试函数"""
    try:
        # 设置数据库
        setup_db()
        
        # 创建数据库会话
        db = SessionLocal()
        
        try:
            # 运行测试
            novel = test_novel_creation(db)
            chapters = test_chapter_creation(db, novel)
            character = test_character_creation(db, novel)
            relationship = test_relationship_creation(db, novel)
            
            # 测试级联删除
            test_cascade_delete(db, novel)
            
            logger.info("所有测试通过！")
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error(f"测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main() 