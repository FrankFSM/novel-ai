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
    
    # 获取章节信息，用于返回结果
    chapter_info = {}
    all_chapters = db.query(novel.Chapter).filter(
        novel.Chapter.novel_id == novel_id
    ).all()
    for chapter in all_chapters:
        chapter_info[chapter.id] = {
            "title": chapter.title,
            "number": chapter.number
        }
    
    # 如果不是强制刷新，检查是否已有角色分析结果
    if not force_refresh and db_novel.characters:
        logger.info(f"使用现有角色数据，novel_id={novel_id}")
        
        # 按角色名聚合数据，获取所有章节中该角色的综合信息
        character_aggregated = {}
        for character in db_novel.characters:
            if character.name not in character_aggregated:
                character_aggregated[character.name] = {
                    "id": character.id,
                    "name": character.name,
                    "alias": character.alias or [],
                    "description": character.description or "",
                    "first_appearance": character.first_appearance,
                    "importance": character.importance or 1,
                    "chapters": [],
                    "chapter_info": []
                }
            
            # 如果角色有关联章节，添加到章节列表
            if character.chapter_id:
                character_aggregated[character.name]["chapters"].append(character.chapter_id)
                character_aggregated[character.name]["chapter_info"].append({
                    "chapter_id": character.chapter_id,
                    "chapter_title": chapter_info.get(character.chapter_id, {}).get("title", f"第{chapter_info.get(character.chapter_id, {}).get('number', '?')}章"),
                    "chapter_number": chapter_info.get(character.chapter_id, {}).get("number", 0),
                    "description": character.description
                })
        
        return list(character_aggregated.values())
    
    # 如果是强制刷新，先删除现有角色数据
    if force_refresh:
        deleted = db.query(novel.Character).filter(
            novel.Character.novel_id == novel_id
        ).delete()
        logger.info(f"已删除{deleted}条现有角色数据")
    
    # 计数和聚合数据容器
    created_count = 0
    character_aggregated = {}
    
    # 对每个章节单独进行分析
    for chapter in all_chapters:
        # 获取单个章节内容
        chapter_content = novel_service.get_chapter_content(db=db, chapter_id=chapter.id)
        if not chapter_content:
            logger.warning(f"章节内容为空: chapter_id={chapter.id}")
            continue
        
        # 使用AI分析当前章节的角色
        try:
            logger.info(f"调用OpenAI API分析章节角色: chapter_id={chapter.id}")
            # 传递is_chapter_specific=True，告诉模型只分析这个章节中的角色表现
            characters_data = await OpenAIClient.analyze_characters(chapter_content, is_chapter_specific=True)
            logger.info(f"成功获取章节角色分析结果: chapter_id={chapter.id}, 共{len(characters_data)}个角色")
            
            # 为该章节创建角色记录
            for character_data in characters_data:
                # 创建该章节的角色记录
                new_character = novel.Character(
                    novel_id=novel_id,
                    chapter_id=chapter.id,
                    name=character_data["name"],
                    alias=character_data.get("alias", []),
                    description=character_data.get("description", ""),
                    importance=character_data.get("importance", 1),
                    first_appearance=character_data.get("first_appearance")
                )
                db.add(new_character)
                created_count += 1
                
                # 聚合数据用于返回
                if character_data["name"] not in character_aggregated:
                    character_aggregated[character_data["name"]] = {
                        "name": character_data["name"],
                        "alias": character_data.get("alias", []),
                        "description": character_data.get("description", ""),
                        "importance": character_data.get("importance", 1),
                        "first_appearance": character_data.get("first_appearance"),
                        "chapters": [chapter.id],
                        "chapter_info": [{
                            "chapter_id": chapter.id,
                            "chapter_title": chapter.title,
                            "chapter_number": chapter.number,
                            "description": character_data.get("description", "")
                        }]
                    }
                else:
                    # 如果角色已存在，更新重要性和描述（如果新信息更详细）
                    if character_data.get("importance", 0) > character_aggregated[character_data["name"]]["importance"]:
                        character_aggregated[character_data["name"]]["importance"] = character_data.get("importance", 1)
                    
                    # 合并描述，如果新描述更详细
                    if len(character_data.get("description", "")) > len(character_aggregated[character_data["name"]]["description"]):
                        character_aggregated[character_data["name"]]["description"] = character_data.get("description", "")
                    
                    # 合并别名
                    existing_aliases = set(character_aggregated[character_data["name"]]["alias"])
                    new_aliases = set(character_data.get("alias", []))
                    merged_aliases = list(existing_aliases.union(new_aliases))
                    character_aggregated[character_data["name"]]["alias"] = merged_aliases
                    
                    # 添加章节信息
                    character_aggregated[character_data["name"]]["chapters"].append(chapter.id)
                    character_aggregated[character_data["name"]]["chapter_info"].append({
                        "chapter_id": chapter.id,
                        "chapter_title": chapter.title,
                        "chapter_number": chapter.number,
                        "description": character_data.get("description", "")
                    })
        except Exception as e:
            logger.error(f"分析章节角色失败: chapter_id={chapter.id}, error={str(e)}")
            # 继续处理下一个章节，不中断整个流程
            continue
    
    db.commit()
    logger.info(f"角色分析处理完成: 创建了{created_count}个角色记录")
    
    # 获取新创建的角色ID
    for character_name, data in character_aggregated.items():
        character = db.query(novel.Character).filter(
            novel.Character.novel_id == novel_id,
            novel.Character.name == character_name
        ).first()
        if character:
            data["id"] = character.id
    
    return list(character_aggregated.values())

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

async def analyze_characters_by_chapter(db: Session, novel_id: int, start_chapter_id: int, end_chapter_id: int) -> List[Dict[str, Any]]:
    """根据章节范围分析小说角色
    
    Args:
        db: 数据库会话
        novel_id: 小说ID
        start_chapter_id: 起始章节ID
        end_chapter_id: 结束章节ID
        
    Returns:
        角色分析结果列表
    """
    logger.info(f"开始分析章节范围内角色: novel_id={novel_id}, start_chapter={start_chapter_id}, end_chapter={end_chapter_id}")
    
    # 验证小说存在
    db_novel = novel_service.get_novel(db=db, novel_id=novel_id)
    if not db_novel:
        raise ValueError("小说不存在")
    
    # 验证章节范围
    if start_chapter_id > end_chapter_id:
        raise ValueError("起始章节ID不能大于结束章节ID")
    
    # 获取指定章节范围
    chapters = db.query(novel.Chapter).filter(
        novel.Chapter.novel_id == novel_id,
        novel.Chapter.id >= start_chapter_id,
        novel.Chapter.id <= end_chapter_id
    ).order_by(novel.Chapter.number).all()
    
    if not chapters:
        raise ValueError("找不到指定的章节范围")
    
    # 记录本次分析涉及的章节
    analyzed_chapter_ids = [chapter.id for chapter in chapters]
    
    # 删除这些章节的现有角色数据
    deleted = db.query(novel.Character).filter(
        novel.Character.novel_id == novel_id,
        novel.Character.chapter_id.in_(analyzed_chapter_ids)
    ).delete(synchronize_session=False)
    logger.info(f"已删除指定章节范围内的{deleted}条现有角色数据")
    
    # 创建记录所有创建角色的字典
    created_count = 0
    character_aggregated = {}
    
    # 每个章节单独分析角色，而不是一次性分析所有章节
    for chapter in chapters:
        # 获取单个章节的内容
        chapter_content = novel_service.get_chapter_content(db=db, chapter_id=chapter.id)
        if not chapter_content:
            logger.warning(f"章节内容为空: chapter_id={chapter.id}")
            continue
        
        # 使用AI分析单个章节的角色
        try:
            logger.info(f"调用OpenAI API分析章节角色: chapter_id={chapter.id}")
            # 传递is_chapter_specific=True，告诉模型只分析这个章节中的角色表现
            characters_data = await OpenAIClient.analyze_characters(chapter_content, is_chapter_specific=True)
            logger.info(f"成功获取章节角色分析结果，chapter_id={chapter.id}，共{len(characters_data)}个角色")
            
            # 为该章节创建角色记录
            for character_data in characters_data:
                new_character = novel.Character(
                    novel_id=novel_id,
                    chapter_id=chapter.id,
                    name=character_data["name"],
                    alias=character_data.get("alias", []),
                    description=character_data.get("description", ""),
                    importance=character_data.get("importance", 1),
                    first_appearance=character_data.get("first_appearance")
                )
                db.add(new_character)
                created_count += 1
                
                # 聚合数据用于返回
                if character_data["name"] not in character_aggregated:
                    character_aggregated[character_data["name"]] = {
                        "name": character_data["name"],
                        "alias": character_data.get("alias", []),
                        "description": character_data.get("description", ""),
                        "importance": character_data.get("importance", 1),
                        "first_appearance": character_data.get("first_appearance"),
                        "chapters": [chapter.id],
                        "chapter_info": [{
                            "chapter_id": chapter.id,
                            "chapter_title": chapter.title,
                            "chapter_number": chapter.number,
                            "description": character_data.get("description", "")
                        }]
                    }
                else:
                    # 如果角色已存在，更新重要性和章节信息
                    if character_data.get("importance", 0) > character_aggregated[character_data["name"]]["importance"]:
                        character_aggregated[character_data["name"]]["importance"] = character_data.get("importance", 1)
                    
                    # 合并描述，如果新描述更详细
                    if len(character_data.get("description", "")) > len(character_aggregated[character_data["name"]]["description"]):
                        character_aggregated[character_data["name"]]["description"] = character_data.get("description", "")
                    
                    # 合并别名
                    existing_aliases = set(character_aggregated[character_data["name"]]["alias"])
                    new_aliases = set(character_data.get("alias", []))
                    merged_aliases = list(existing_aliases.union(new_aliases))
                    character_aggregated[character_data["name"]]["alias"] = merged_aliases
                    
                    # 添加章节信息
                    character_aggregated[character_data["name"]]["chapters"].append(chapter.id)
                    character_aggregated[character_data["name"]]["chapter_info"].append({
                        "chapter_id": chapter.id,
                        "chapter_title": chapter.title,
                        "chapter_number": chapter.number,
                        "description": character_data.get("description", "")
                    })
        
        except Exception as e:
            logger.error(f"分析章节角色失败: chapter_id={chapter.id}, error={str(e)}")
            # 继续处理下一个章节，不中断整个流程
            continue
    
    db.commit()
    logger.info(f"章节角色分析处理完成: 创建了{created_count}个角色记录")
    
    # 获取所有角色的综合信息
    all_characters = {}
    
    # 获取分析的章节中的角色
    for character_name, data in character_aggregated.items():
        character = db.query(novel.Character).filter(
            novel.Character.novel_id == novel_id,
            novel.Character.name == character_name,
            novel.Character.chapter_id.in_(analyzed_chapter_ids)
        ).first()
        
        if character:
            all_characters[character_name] = {
                "id": character.id,
                "name": character_name,
                "alias": data["alias"],
                "description": data["description"],
                "importance": data["importance"],
                "first_appearance": data["first_appearance"],
                "chapters": data["chapters"],
                "chapter_info": data["chapter_info"]
            }
    
    # 再获取其他章节的角色信息
    other_characters = db.query(novel.Character).filter(
        novel.Character.novel_id == novel_id,
        novel.Character.chapter_id.notin_(analyzed_chapter_ids)
    ).all()
    
    # 获取所有章节信息，用于标题显示
    chapter_info = {}
    all_chapters = db.query(novel.Chapter).filter(
        novel.Chapter.novel_id == novel_id
    ).all()
    for chapter in all_chapters:
        chapter_info[chapter.id] = {
            "title": chapter.title,
            "number": chapter.number
        }
    
    # 合并其他章节中的角色信息
    for character in other_characters:
        if character.name in all_characters:
            # 合并已有角色的章节信息
            if character.chapter_id and character.chapter_id not in all_characters[character.name]["chapters"]:
                all_characters[character.name]["chapters"].append(character.chapter_id)
                all_characters[character.name]["chapter_info"].append({
                    "chapter_id": character.chapter_id,
                    "chapter_title": chapter_info.get(character.chapter_id, {}).get("title", ""),
                    "chapter_number": chapter_info.get(character.chapter_id, {}).get("number", 0),
                    "description": character.description
                })
        else:
            # 添加不在分析章节中的角色
            chapters = [character.chapter_id] if character.chapter_id else []
            chapter_info_list = []
            if character.chapter_id:
                chapter_info_list.append({
                    "chapter_id": character.chapter_id,
                    "chapter_title": chapter_info.get(character.chapter_id, {}).get("title", ""),
                    "chapter_number": chapter_info.get(character.chapter_id, {}).get("number", 0),
                    "description": character.description
                })
            
            all_characters[character.name] = {
                "id": character.id,
                "name": character.name,
                "alias": character.alias or [],
                "description": character.description or "",
                "importance": character.importance or 1,
                "first_appearance": character.first_appearance,
                "chapters": chapters,
                "chapter_info": chapter_info_list
            }
    
    return list(all_characters.values())

def get_novel_characters_without_analysis(db: Session, novel_id: int) -> List[Dict[str, Any]]:
    """获取小说中的所有角色，不触发分析
    
    Args:
        db: 数据库会话
        novel_id: 小说ID
        
    Returns:
        角色数据列表，如果没有角色则返回空列表
    """
    logger.info(f"获取小说角色(无需分析): novel_id={novel_id}")
    
    # 获取小说
    db_novel = novel_service.get_novel(db=db, novel_id=novel_id)
    if not db_novel:
        raise ValueError("小说不存在")
    
    # 查询所有属于该小说的角色
    characters = db.query(novel.Character).filter(
        novel.Character.novel_id == novel_id
    ).all()
    
    # 如果没有角色，直接返回空列表
    if not characters:
        logger.info(f"小说没有角色数据: novel_id={novel_id}")
        return []
    
    # 获取章节信息，用于返回结果
    chapter_info = {}
    all_chapters = db.query(novel.Chapter).filter(
        novel.Chapter.novel_id == novel_id
    ).all()
    for chapter in all_chapters:
        chapter_info[chapter.id] = {
            "title": chapter.title,
            "number": chapter.number
        }
    
    # 按角色名聚合数据
    character_aggregated = {}
    for character in characters:
        if character.name not in character_aggregated:
            character_aggregated[character.name] = {
                "id": character.id,
                "name": character.name,
                "alias": character.alias or [],
                "description": character.description or "",
                "first_appearance": character.first_appearance,
                "importance": character.importance or 1,
                "chapters": [],
                "chapter_info": []
            }
        
        # 如果角色有关联章节，添加到章节列表
        if character.chapter_id and character.chapter_id not in character_aggregated[character.name]["chapters"]:
            character_aggregated[character.name]["chapters"].append(character.chapter_id)
            character_aggregated[character.name]["chapter_info"].append({
                "chapter_id": character.chapter_id,
                "chapter_title": chapter_info.get(character.chapter_id, {}).get("title", ""),
                "chapter_number": chapter_info.get(character.chapter_id, {}).get("number", 0),
                "description": character.description
            })
    
    # 返回聚合后的角色数据
    return list(character_aggregated.values()) 