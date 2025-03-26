import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.models import novel
from app.models.novel import Novel, Character, Location, Event, EventParticipation
from app.services import novel_service
from app.core.config import settings
from app.core.openai_client import OpenAIClient

# 设置日志
logger = logging.getLogger(__name__)

async def analyze_novel_events(db: Session, novel_id: int) -> List[Dict[str, Any]]:
    """
    分析小说中的事件
    
    Args:
        db: 数据库会话
        novel_id: 小说ID
        
    Returns:
        List[Dict[str, Any]]: 分析得到的事件列表
    """
    logger.info(f"开始分析小说ID {novel_id} 的事件")
    
    # 1. 检查小说是否存在
    novel_obj = db.query(novel.Novel).filter(novel.Novel.id == novel_id).first()
    if not novel_obj:
        logger.error(f"小说ID {novel_id} 不存在")
        raise ValueError(f"小说ID {novel_id} 不存在")
    
    # 2. 获取小说内容
    content = novel_service.get_novel_chapters_content(db=db, novel_id=novel_id)
    if not content:
        logger.warning(f"小说ID {novel_id} 没有内容，无法分析事件")
        return []
    
    # 3. 获取小说角色
    characters = db.query(novel.Character).filter(novel.Character.novel_id == novel_id).all()
    if not characters:
        logger.warning(f"小说ID {novel_id} 没有角色数据，无法关联事件与角色")
        return []
    
    # 4. 获取小说地点
    locations = db.query(novel.Location).filter(novel.Location.novel_id == novel_id).all()
    if not locations:
        logger.warning(f"小说ID {novel_id} 没有地点数据，无法关联事件与地点")
        return []
    
    # 5. 暂时不使用AI分析，只提供一些基本的示例事件
    # 在实际应用中，这里可以使用OpenAI API分析小说内容并提取事件
    try:
        # 清除现有事件数据
        db.query(novel.EventParticipation).filter(
            novel.EventParticipation.event_id.in_(
                db.query(novel.Event.id).filter(novel.Event.novel_id == novel_id)
            )
        ).delete(synchronize_session=False)
        
        db.query(novel.Event).filter(novel.Event.novel_id == novel_id).delete()
        db.commit()
        
        # 添加一些示例事件（实际应用中应该通过AI分析得出）
        sample_events = [
            {
                "name": "故事开始",
                "description": "主角登场并介绍了背景设定",
                "chapter_id": 1,
                "time_description": "故事伊始",
                "importance": 5,
                "location_id": locations[0].id if locations else None,
                "participants": [
                    {"character_id": characters[0].id, "role": "主角", "importance": 5} if characters else None
                ]
            },
            {
                "name": "关键冲突",
                "description": "主角遇到了重大挑战",
                "chapter_id": 3,
                "time_description": "故事中期",
                "importance": 4,
                "location_id": locations[1].id if len(locations) > 1 else (locations[0].id if locations else None),
                "participants": [
                    {"character_id": characters[0].id, "role": "挑战者", "importance": 4} if characters else None,
                    {"character_id": characters[1].id, "role": "对手", "importance": 3} if len(characters) > 1 else None
                ]
            }
        ]
        
        # 将示例事件保存到数据库
        for event_data in sample_events:
            participants = event_data.pop("participants", [])
            
            # 创建事件
            new_event = novel.Event(
                novel_id=novel_id,
                **{k: v for k, v in event_data.items() if v is not None}
            )
            db.add(new_event)
            db.flush()  # 获取新创建事件的ID
            
            # 添加事件参与者
            for participant in participants:
                if participant and participant["character_id"]:
                    event_participation = novel.EventParticipation(
                        event_id=new_event.id,
                        character_id=participant["character_id"],
                        role=participant.get("role")
                    )
                    db.add(event_participation)
        
        db.commit()
        logger.info(f"成功为小说ID {novel_id} 添加了 {len(sample_events)} 个示例事件")
        
        # 返回新创建的事件列表
        return sample_events
        
    except Exception as e:
        db.rollback()
        logger.error(f"分析小说事件失败: {str(e)}")
        raise ValueError(f"分析小说事件失败: {str(e)}")

async def get_novel_events(db: Session, novel_id: int, force_refresh: bool = False) -> Dict[str, Any]:
    """
    获取小说中的所有事件
    
    Args:
        db: 数据库会话
        novel_id: 小说ID
        force_refresh: 是否强制刷新分析结果
        
    Returns:
        Dict[str, Any]: 包含事件列表和元数据的字典
    """
    logger.info(f"获取小说ID为 {novel_id} 的事件列表，force_refresh={force_refresh}")
    
    # 1. 检查小说是否存在
    novel_obj = db.query(novel.Novel).filter(novel.Novel.id == novel_id).first()
    if not novel_obj:
        logger.error(f"小说ID {novel_id} 不存在")
        raise ValueError(f"小说ID {novel_id} 不存在")
    
    # 2. 检查角色数据是否存在
    characters_exist = db.query(novel.Character).filter(novel.Character.novel_id == novel_id).count() > 0
    logger.info(f"小说ID {novel_id} 的角色数据存在性: {characters_exist}")
    
    # 3. 检查地点数据是否存在
    locations_exist = db.query(novel.Location).filter(novel.Location.novel_id == novel_id).count() > 0
    logger.info(f"小说ID {novel_id} 的地点数据存在性: {locations_exist}")
    
    # 4. 如果force_refresh为True且角色和地点数据都存在，则重新分析事件
    if force_refresh and characters_exist and locations_exist:
        logger.info(f"开始强制刷新小说ID {novel_id} 的事件分析")
        await analyze_novel_events(db, novel_id)
    
    # 5. 从数据库获取事件
    events = []
    db_events = db.query(novel.Event).filter(novel.Event.novel_id == novel_id).all()
    events_count = len(db_events)
    logger.info(f"从数据库获取到 {events_count} 个事件")
    
    for event in db_events:
        # 获取事件参与者
        participants = []
        event_participants = db.query(novel.EventParticipation).filter(
            novel.EventParticipation.event_id == event.id
        ).all()
        
        for ep in event_participants:
            character = db.query(novel.Character).filter(novel.Character.id == ep.character_id).first()
            if character:
                participants.append({
                    "id": character.id,
                    "name": character.name,
                    "role": ep.role,
                    "importance": character.importance or 1
                })
        
        # 获取事件地点
        location = None
        if event.location_id:
            location_obj = db.query(novel.Location).filter(novel.Location.id == event.location_id).first()
            if location_obj:
                location = {
                    "id": location_obj.id,
                    "name": location_obj.name
                }
        
        events.append({
            "id": event.id,
            "name": event.name,
            "description": event.description,
            "chapter_id": event.chapter_id,
            "time_description": event.time_description,
            "importance": event.importance,
            "participants": participants,
            "location": location
        })
    
    # 6. 构造响应
    response = {
        "events": events,
        "metadata": {
            "characters_exist": characters_exist,
            "locations_exist": locations_exist,
            "events_count": events_count
        }
    }
    
    return response

async def get_event_details(db: Session, event_id: int) -> Dict[str, Any]:
    """获取事件详细信息
    
    Args:
        db: 数据库会话
        event_id: 事件ID
        
    Returns:
        事件详细信息
    """
    # 获取事件
    event = db.query(novel.Event).filter(novel.Event.id == event_id).first()
    if not event:
        raise ValueError("事件不存在")
    
    # 获取事件的地点信息
    location = None
    if event.location_id:
        location_obj = db.query(novel.Location).filter(novel.Location.id == event.location_id).first()
        if location_obj:
            location = {
                "id": location_obj.id,
                "name": location_obj.name,
                "description": location_obj.description
            }
    
    # 获取事件的参与角色
    participants = []
    participations = db.query(novel.EventParticipation).filter(
        novel.EventParticipation.event_id == event.id
    ).all()
    
    for participation in participations:
        character = db.query(novel.Character).filter(
            novel.Character.id == participation.character_id
        ).first()
        
        if character:
            participants.append({
                "id": character.id,
                "name": character.name,
                "role": participation.role,
                "importance": character.importance or 1
            })
    
    # 获取相关的章节内容片段（如果有章节ID）
    context_excerpt = None
    if event.chapter_id:
        chapter = db.query(novel.Chapter).filter(
            novel.Chapter.id == event.chapter_id
        ).first()
        
        if chapter:
            # 提取章节中相关内容的片段，这里简化处理，实际可能需要更复杂的文本处理
            content = chapter.content
            if content and len(content) > 500:
                # 简单截取500个字符作为上下文，实际应用中可能需要更智能的提取
                context_excerpt = content[:500] + "..."
            else:
                context_excerpt = content
    
    # 构建结果
    result = {
        "id": event.id,
        "name": event.name,
        "description": event.description,
        "chapter_id": event.chapter_id,
        "chapter_title": chapter.title if event.chapter_id and chapter else None,
        "importance": event.importance,
        "time_description": event.time_description,
        "location": location,
        "participants": participants,
        "context_excerpt": context_excerpt
    }
    
    return result

async def analyze_event_significance(db: Session, event_id: int) -> Dict[str, Any]:
    """分析事件的重要性和影响
    
    Args:
        db: 数据库会话
        event_id: 事件ID
        
    Returns:
        事件重要性分析结果
    """
    # 获取事件
    event = db.query(novel.Event).filter(novel.Event.id == event_id).first()
    if not event:
        raise ValueError("事件不存在")
    
    # 获取小说
    novel_data = novel_service.get_novel(db=db, novel_id=event.novel_id)
    if not novel_data:
        raise ValueError("小说不存在")
    
    # 获取小说内容
    content = novel_service.get_novel_chapters_content(db=db, novel_id=event.novel_id)
    if not content:
        return {
            "name": event.name,
            "significance": [],
            "impact": [],
            "analysis": "无法分析，小说内容为空"
        }
    
    # 使用AI分析事件重要性
    try:
        # 这里应该调用OpenAI API分析事件重要性
        # 目前返回一个模拟的结果
        return {
            "name": event.name,
            "significance": [
                "关键转折点",
                "人物关系变化",
                "情节推进"
            ],
            "impact": [
                {
                    "aspect": "情节影响",
                    "description": "该事件导致了主线情节的重大转变",
                    "evidence": "事件后续章节中情节发展明显改变"
                },
                {
                    "aspect": "角色成长",
                    "description": "主角在此事件中经历了重要成长",
                    "evidence": "事件后主角行为方式和决策有明显变化"
                }
            ],
            "analysis": f"{event.name}是小说中的重要事件，对情节走向和角色发展产生了深远影响。"
        }
        
    except Exception as e:
        logger.error(f"事件重要性分析失败: {str(e)}")
        raise 