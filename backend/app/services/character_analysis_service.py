from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

from app.models import novel
from app.services import novel_service
from app.core.openai_client import OpenAIClient

logger = logging.getLogger(__name__)

async def analyze_novel_characters(db: Session, novel_id: int, force_refresh: bool = False) -> List[Dict[str, Any]]:
    """分析小说中的人物角色
    
    Args:
        db: 数据库会话
        novel_id: 小说ID
        force_refresh: 是否强制刷新分析结果
        
    Returns:
        角色分析结果列表
    """
    logger.info(f"开始分析小说人物: novel_id={novel_id}, force_refresh={force_refresh}")
    
    # 获取小说
    db_novel = novel_service.get_novel(db=db, novel_id=novel_id)
    if not db_novel:
        raise ValueError("小说不存在")
    
    # 如果不是强制刷新，检查是否已有角色分析结果
    if not force_refresh and db_novel.characters:
        logger.info(f"使用现有角色数据，novel_id={novel_id}")
        return [
            {
                "id": character.id,
                "name": character.name,
                "alias": character.alias,
                "description": character.description,
                "first_appearance": character.first_appearance,
                "importance": character.importance
            }
            for character in db_novel.characters
        ]
    
    # 获取小说内容
    logger.info(f"需要分析角色，获取小说内容: novel_id={novel_id}")
    content = novel_service.get_novel_chapters_content(db=db, novel_id=novel_id)
    if not content:
        raise ValueError("小说内容为空")
    
    # 使用AI分析角色
    try:
        logger.info("调用OpenAI API分析角色...")
        characters_data = await OpenAIClient.analyze_characters(content)
        logger.info(f"成功获取角色分析结果，共{len(characters_data)}个角色")
        
        # 记录所有操作，用于调试和记录
        created_count = 0
        updated_count = 0
        
        # 保存分析结果到数据库
        for character_data in characters_data:
            # 检查角色是否已存在
            existing = db.query(novel.Character).filter(
                novel.Character.novel_id == novel_id,
                novel.Character.name == character_data["name"]
            ).first()
            
            if existing:
                # 更新现有角色
                logger.info(f"更新现有角色: {character_data['name']}")
                existing.description = character_data.get("description", existing.description)
                existing.alias = character_data.get("alias", existing.alias)
                existing.importance = character_data.get("importance", existing.importance)
                updated_count += 1
            else:
                # 创建新角色
                logger.info(f"创建新角色: {character_data['name']}")
                new_character = novel.Character(
                    novel_id=novel_id,
                    name=character_data["name"],
                    alias=character_data.get("alias", []),
                    description=character_data.get("description", ""),
                    importance=character_data.get("importance", 1)
                )
                db.add(new_character)
                created_count += 1
        
        db.commit()
        logger.info(f"角色分析处理完成: 创建了{created_count}个新角色，更新了{updated_count}个现有角色")
        
        # 返回更新后的角色列表
        updated_characters = db.query(novel.Character).filter(
            novel.Character.novel_id == novel_id
        ).order_by(novel.Character.importance.desc()).all()
        
        return [
            {
                "id": character.id,
                "name": character.name,
                "alias": character.alias,
                "description": character.description,
                "first_appearance": character.first_appearance,
                "importance": character.importance
            }
            for character in updated_characters
        ]
        
    except Exception as e:
        db.rollback()
        logger.error(f"角色分析失败: {str(e)}")
        raise

async def get_character_details(db: Session, character_id: int) -> Dict[str, Any]:
    """获取角色详细信息
    
    Args:
        db: 数据库会话
        character_id: 角色ID
        
    Returns:
        角色详细信息
    """
    # 获取角色
    character = db.query(novel.Character).filter(novel.Character.id == character_id).first()
    if not character:
        raise ValueError("角色不存在")
    
    # 获取角色所有关系
    relationships = []
    
    # 获取从该角色出发的关系
    from_relations = db.query(novel.Relationship).filter(
        novel.Relationship.from_character_id == character_id
    ).all()
    
    for rel in from_relations:
        to_character = db.query(novel.Character).filter(
            novel.Character.id == rel.to_character_id
        ).first()
        
        if to_character:
            relationships.append({
                "id": rel.id,
                "character": {
                    "id": to_character.id,
                    "name": to_character.name
                },
                "relation_type": rel.relation_type,
                "description": rel.description,
                "direction": "to"
            })
    
    # 获取到该角色的关系
    to_relations = db.query(novel.Relationship).filter(
        novel.Relationship.to_character_id == character_id
    ).all()
    
    for rel in to_relations:
        from_character = db.query(novel.Character).filter(
            novel.Character.id == rel.from_character_id
        ).first()
        
        if from_character:
            relationships.append({
                "id": rel.id,
                "character": {
                    "id": from_character.id,
                    "name": from_character.name
                },
                "relation_type": rel.relation_type,
                "description": rel.description,
                "direction": "from"
            })
    
    # 获取角色出现的事件
    events = []
    participations = db.query(novel.EventParticipation).filter(
        novel.EventParticipation.character_id == character_id
    ).all()
    
    for participation in participations:
        event = db.query(novel.Event).filter(
            novel.Event.id == participation.event_id
        ).first()
        
        if event:
            events.append({
                "id": event.id,
                "name": event.name,
                "description": event.description,
                "role": participation.role
            })
    
    # 获取角色拥有的物品
    items = db.query(novel.Item).filter(
        novel.Item.owner_id == character_id
    ).all()
    
    # 构建结果
    result = {
        "id": character.id,
        "name": character.name,
        "alias": character.alias,
        "description": character.description,
        "first_appearance": character.first_appearance,
        "relationships": relationships,
        "events": events,
        "items": [
            {
                "id": item.id,
                "name": item.name,
                "description": item.description
            }
            for item in items
        ]
    }
    
    return result

async def analyze_character_personality(db: Session, character_id: int) -> Dict[str, Any]:
    """分析角色性格和特点
    
    Args:
        db: 数据库会话
        character_id: 角色ID
        
    Returns:
        角色性格分析结果
    """
    # 获取角色
    character = db.query(novel.Character).filter(novel.Character.id == character_id).first()
    if not character:
        raise ValueError("角色不存在")
    
    # 获取小说
    novel_data = novel_service.get_novel(db=db, novel_id=character.novel_id)
    if not novel_data:
        raise ValueError("小说不存在")
    
    # 获取小说内容
    content = novel_service.get_novel_chapters_content(db=db, novel_id=character.novel_id)
    if not content:
        return {
            "name": character.name,
            "personality": [],
            "traits": [],
            "analysis": "无法分析，小说内容为空"
        }
    
    # 使用AI分析角色性格
    try:
        analysis_result = await OpenAIClient.analyze_character_personality(content, character.name)
        
        # 更新角色描述
        if "description" in analysis_result and analysis_result["description"]:
            character.description = analysis_result["description"]
            db.commit()
        
        return analysis_result
        
    except Exception as e:
        logger.error(f"角色性格分析失败: {str(e)}")
        raise 