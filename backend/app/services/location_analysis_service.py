from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging
import re

from app.models import novel
from app.services import novel_service
from app.core.openai_client import OpenAIClient

logger = logging.getLogger(__name__)

def filter_invalid_locations(locations_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """过滤掉不太可能是地点的条目
    
    Args:
        locations_list: 地点列表
        
    Returns:
        过滤后的地点列表
    """
    filtered_locations = []
    
    # 可能是物品或收藏品的关键词
    non_location_keywords = [
        '藏品', '收藏', '瓷器', '字画', '宝剑', '法宝', '丹药', '秘籍',
        '宝物', '珍品', '玉器', '兵器', '装备', '道具', '功法', '神通'
    ]
    
    for location in locations_list:
        name = location.get("name", "").strip()
        description = location.get("description", "").strip()
        
        # 检查名称是否包含非地点关键词
        is_non_location = False
        for keyword in non_location_keywords:
            if keyword in name:
                logger.info(f"跳过可能的非地点条目: {name} (含关键词: {keyword})")
                is_non_location = True
                break
        
        # 如果名称太短且没有描述，可能不是有效地点
        if len(name) <= 2 and not description:
            logger.info(f"跳过可能的非地点条目: {name} (名称太短且无描述)")
            is_non_location = True
        
        # 确认有描述且描述中提及空间特性的更可能是地点
        location_indicators = ['位于', '地方', '场所', '区域', '空间', '地点', '城市', '建筑', '山脉', '府邸', '宫殿']
        has_location_indicator = False
        for indicator in location_indicators:
            if indicator in description:
                has_location_indicator = True
                break
        
        # 如果明确不是地点，跳过；如果有明确地点特征，保留；其他情况默认保留
        if is_non_location and not has_location_indicator:
            continue
        
        filtered_locations.append(location)
    
    logger.info(f"地点过滤: 原始数量 {len(locations_list)}，过滤后数量 {len(filtered_locations)}")
    return filtered_locations

async def analyze_novel_locations(db: Session, novel_id: int, force_refresh: bool = False) -> List[Dict[str, Any]]:
    """分析小说中的地点
    
    Args:
        db: 数据库会话
        novel_id: 小说ID
        force_refresh: 是否强制刷新分析结果
        
    Returns:
        地点分析结果列表
    """
    logger.info(f"开始分析小说地点: novel_id={novel_id}, force_refresh={force_refresh}")
    
    # 获取小说
    db_novel = novel_service.get_novel(db=db, novel_id=novel_id)
    if not db_novel:
        raise ValueError("小说不存在")
    
    # 如果不是强制刷新，检查是否已有地点分析结果
    if not force_refresh and db_novel.locations:
        logger.info(f"使用现有地点数据，novel_id={novel_id}")
        return [
            {
                "id": location.id,
                "name": location.name,
                "description": location.description,
                "parent_id": location.parent_id,
                "events_count": len(location.events) if hasattr(location, "events") else 0
            }
            for location in db_novel.locations
        ]
    
    # 获取小说内容
    logger.info(f"需要分析地点，获取小说内容: novel_id={novel_id}")
    content = novel_service.get_novel_chapters_content(db=db, novel_id=novel_id)
    if not content:
        raise ValueError("小说内容为空")
    
    # 使用AI分析地点
    try:
        logger.info("调用OpenAI API分析地点...")
        locations_data = await OpenAIClient.extract_entities(content)
        locations_list = locations_data.get("locations", [])
        logger.info(f"成功获取地点分析结果，共{len(locations_list)}个地点")
        
        # 过滤不太可能是地点的条目
        locations_list = filter_invalid_locations(locations_list)
        
        # 记录所有操作，用于调试和记录
        created_count = 0
        updated_count = 0
        
        # 保存分析结果到数据库
        for location_data in locations_list:
            # 检查地点是否已存在
            existing = db.query(novel.Location).filter(
                novel.Location.novel_id == novel_id,
                novel.Location.name.ilike(location_data["name"].strip())
            ).first()
            
            if existing:
                # 更新现有地点
                logger.info(f"更新现有地点: {location_data['name']}")
                existing.description = location_data.get("description", existing.description)
                # 更新重要性（如果提供）
                if "importance" in location_data and location_data["importance"]:
                    existing.importance = location_data["importance"]
                updated_count += 1
            else:
                # 创建新地点
                logger.info(f"创建新地点: {location_data['name']}")
                new_location = novel.Location(
                    novel_id=novel_id,
                    name=location_data["name"],
                    description=location_data.get("description", ""),
                    importance=location_data.get("importance", 1)  # 默认值为1
                )
                db.add(new_location)
                created_count += 1
        
        # 处理地点的父子关系
        for location_data in locations_list:
            if "parent" in location_data and location_data["parent"]:
                child_location = db.query(novel.Location).filter(
                    novel.Location.novel_id == novel_id,
                    novel.Location.name.ilike(location_data["name"].strip())
                ).first()
                
                parent_location = db.query(novel.Location).filter(
                    novel.Location.novel_id == novel_id,
                    novel.Location.name.ilike(location_data["parent"].strip())
                ).first()
                
                if child_location and parent_location:
                    child_location.parent_id = parent_location.id
        
        db.commit()
        logger.info(f"地点分析处理完成: 创建了{created_count}个新地点，更新了{updated_count}个现有地点")
        
        # 返回更新后的地点列表
        updated_locations = db.query(novel.Location).filter(
            novel.Location.novel_id == novel_id
        ).all()
        
        return [
            {
                "id": location.id,
                "name": location.name,
                "description": location.description,
                "parent_id": location.parent_id,
                "events_count": len(location.events) if hasattr(location, "events") else 0
            }
            for location in updated_locations
        ]
        
    except Exception as e:
        db.rollback()
        logger.error(f"地点分析失败: {str(e)}")
        raise

async def get_location_details(db: Session, location_id: int) -> Dict[str, Any]:
    """获取地点详细信息
    
    Args:
        db: 数据库会话
        location_id: 地点ID
        
    Returns:
        地点详细信息
    """
    # 获取地点
    location = db.query(novel.Location).filter(novel.Location.id == location_id).first()
    if not location:
        raise ValueError("地点不存在")
    
    # 获取该地点发生的事件
    events = db.query(novel.Event).filter(
        novel.Event.location_id == location_id
    ).all()
    
    # 获取地点的子地点
    sub_locations = db.query(novel.Location).filter(
        novel.Location.parent_id == location_id
    ).all()
    
    # 获取地点的父地点
    parent_location = None
    if location.parent_id:
        parent = db.query(novel.Location).filter(
            novel.Location.id == location.parent_id
        ).first()
        if parent:
            parent_location = {
                "id": parent.id,
                "name": parent.name,
                "description": parent.description
            }
    
    # 获取在此地点出现过的角色
    characters = set()
    for event in events:
        participations = db.query(novel.EventParticipation).filter(
            novel.EventParticipation.event_id == event.id
        ).all()
        
        for participation in participations:
            character = db.query(novel.Character).filter(
                novel.Character.id == participation.character_id
            ).first()
            
            if character:
                characters.add((character.id, character.name, character.importance or 1))
    
    # 构建结果
    result = {
        "id": location.id,
        "name": location.name,
        "description": location.description,
        "parent": parent_location,
        "sub_locations": [
            {
                "id": sub.id,
                "name": sub.name,
                "description": sub.description
            }
            for sub in sub_locations
        ],
        "events": [
            {
                "id": event.id,
                "name": event.name,
                "description": event.description,
                "chapter_id": event.chapter_id,
                "importance": event.importance,
                "time_description": event.time_description
            }
            for event in events
        ],
        "characters": [
            {
                "id": char_id,
                "name": char_name,
                "importance": importance
            }
            for char_id, char_name, importance in sorted(characters, key=lambda x: x[2], reverse=True)
        ]
    }
    
    return result

async def analyze_location_significance(db: Session, location_id: int) -> Dict[str, Any]:
    """分析地点的重要性和特点
    
    Args:
        db: 数据库会话
        location_id: 地点ID
        
    Returns:
        地点重要性分析结果
    """
    # 获取地点
    location = db.query(novel.Location).filter(novel.Location.id == location_id).first()
    if not location:
        raise ValueError("地点不存在")
    
    # 获取小说
    novel_data = novel_service.get_novel(db=db, novel_id=location.novel_id)
    if not novel_data:
        raise ValueError("小说不存在")
    
    # 获取小说内容
    content = novel_service.get_novel_chapters_content(db=db, novel_id=location.novel_id)
    if not content:
        return {
            "name": location.name,
            "significance": [],
            "features": [],
            "analysis": "无法分析，小说内容为空"
        }
    
    # 使用AI分析地点重要性
    try:
        # 这里应该调用 OpenAI API 分析地点
        # 目前我们先返回一个模拟的结果
        return {
            "name": location.name,
            "significance": [
                "主要场景",
                "关键事件发生地",
                "角色聚集地"
            ],
            "features": [
                {
                    "feature": "环境描写",
                    "description": "小说中对该地点有详尽的环境描写",
                    "evidence": "在多个章节中都有对该地点的细致描写"
                },
                {
                    "feature": "情感连接",
                    "description": "该地点与主角有深厚的情感连接",
                    "evidence": "主角在此地经历了多次重要事件"
                }
            ],
            "analysis": f"{location.name}是小说中的重要场景，多个关键情节在此展开。该地点具有鲜明的特色，作者通过细致的环境描写赋予了其独特的氛围。"
        }
        
    except Exception as e:
        logger.error(f"地点重要性分析失败: {str(e)}")
        raise 