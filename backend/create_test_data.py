#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models import novel

# 创建测试数据
db = SessionLocal()
try:
    # 创建小说
    test_novel = novel.Novel(title='测试小说', author='测试作者', description='这是一个测试小说')
    db.add(test_novel)
    db.commit()
    
    novel_id = test_novel.id
    print(f'创建小说成功，ID: {novel_id}')
    
    # 创建章节
    for i in range(1, 4):
        chapter = novel.Chapter(
            novel_id=novel_id,
            title=f'第{i}章',
            content=f'这是第{i}章的内容，讲述了一个故事。',
            number=i,
            word_count=100
        )
        db.add(chapter)
    db.commit()
    print('创建章节成功')
    
    # 创建角色
    characters = []
    for i in range(1, 4):
        character = novel.Character(
            novel_id=novel_id,
            name=f'角色{i}',
            description=f'这是角色{i}的描述',
            importance=i
        )
        db.add(character)
        db.flush()
        characters.append(character)
    db.commit()
    print('创建角色成功')
    
    # 创建地点
    locations = []
    for i in range(1, 4):
        location = novel.Location(
            novel_id=novel_id,
            name=f'地点{i}',
            description=f'这是地点{i}的描述，一个重要的场所。',
            importance=i
        )
        db.add(location)
        db.flush()
        locations.append(location)
    db.commit()
    print('创建地点成功')
    
    # 创建事件
    events = []
    for i in range(1, 4):
        event = novel.Event(
            novel_id=novel_id,
            name=f'事件{i}',
            description=f'这是事件{i}的描述，发生在地点{i}。',
            chapter_id=i,
            location_id=locations[i-1].id,
            time_description=f'第{i}天',
            importance=i
        )
        db.add(event)
        db.flush()
        events.append(event)
    db.commit()
    print('创建事件成功')
    
    # 创建事件参与关系
    for i in range(1, 4):
        for j in range(1, i+1):
            participation = novel.EventParticipation(
                event_id=events[i-1].id,
                character_id=characters[j-1].id,
                role=f'角色{j}在事件{i}中的角色'
            )
            db.add(participation)
    db.commit()
    print('创建事件参与关系成功')
    
    print(f'所有测试数据创建完成，小说ID: {novel_id}')
    
except Exception as e:
    db.rollback()
    print(f'创建测试数据失败: {str(e)}')
finally:
    db.close() 