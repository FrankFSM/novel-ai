from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
import logging
import networkx as nx

from app.models import novel, schemas
from app.services import novel_service
from app.core.openai_client import OpenAIClient

logger = logging.getLogger(__name__)

async def get_relationship_graph(
    db: Session,
    novel_id: int,
    character_id: Optional[int] = None,
    depth: int = 2,
    force_refresh: bool = False
) -> Dict[str, Any]:
    """获取小说人物关系图
    
    Args:
        db: 数据库会话
        novel_id: 小说ID
        character_id: 可选的中心角色ID
        depth: 关系网络深度
        force_refresh: 是否强制刷新（忽略缓存）
        
    Returns:
        包含节点和边的字典
    """
    # 记录请求参数
    logger.info(f"请求关系图: novel_id={novel_id}, character_id={character_id}, depth={depth}, force_refresh={force_refresh}")
    
    # 获取小说
    novel_obj = novel_service.get_novel(db=db, novel_id=novel_id)
    if not novel_obj:
        raise ValueError("小说不存在")
    
    # 如果不是强制刷新，尝试从数据库获取缓存的关系图
    if not force_refresh:
        logger.info(f"尝试获取缓存数据 (force_refresh={force_refresh})")
        cached_graph = get_cached_relationship_graph(db, novel_id, character_id, depth)
        if cached_graph:
            logger.info(f"从数据库缓存获取关系图数据: novel_id={novel_id}, character_id={character_id}, depth={depth}")
            return cached_graph
    else:
        logger.info(f"强制刷新模式，跳过缓存检查 (force_refresh={force_refresh})")
    
    # 获取小说中已分析的角色列表
    characters = db.query(novel.Character).filter(
        novel.Character.novel_id == novel_id
    ).all()
    
    logger.info(f"找到小说中已分析的角色: {len(characters)}个")
    
    if not characters:
        logger.warning("小说中没有已分析的角色，无法生成关系网络")
        return {"nodes": [], "edges": []}
    
    # 构建角色节点映射
    nodes = []
    character_map = {}
    for i, char in enumerate(characters):
        node_id = i + 1  # 确保节点ID从1开始
        character_map[char.name] = {
            "id": node_id,
            "character_id": char.id,
            "importance": char.importance or 1
        }
        
        # 创建节点
        nodes.append({
            "id": node_id,
            "name": char.name,
            "value": 10 + (char.importance or 1) * 5,  # 基于重要性调整节点大小
            "character_id": char.id,
            "importance": char.importance or 1
        })
    
    # 获取现有的关系数据
    existing_relationships = db.query(novel.Relationship).filter(
        novel.Relationship.novel_id == novel_id
    ).all()
    
    logger.info(f"找到现有关系数据: {len(existing_relationships)}条")
    
    # 从现有关系构建边
    edges = []
    edge_id = 1
    processed_pairs = set()  # 用于跟踪已处理的角色对
    
    for rel in existing_relationships:
        from_char = db.query(novel.Character).filter(
            novel.Character.id == rel.from_character_id
        ).first()
        
        to_char = db.query(novel.Character).filter(
            novel.Character.id == rel.to_character_id
        ).first()
        
        if from_char and to_char and from_char.name in character_map and to_char.name in character_map:
            # 创建一个唯一标识符来避免重复边
            pair_key = f"{min(from_char.id, to_char.id)}-{max(from_char.id, to_char.id)}"
            if pair_key in processed_pairs:
                continue
            
            processed_pairs.add(pair_key)
            
            source_id = character_map[from_char.name]["id"]
            target_id = character_map[to_char.name]["id"]
            
            # 根据角色重要性计算关系重要性
            importance = 0.5 + (from_char.importance or 1) * 0.1 + (to_char.importance or 1) * 0.1
            
            edges.append({
                "id": edge_id,
                "source_id": source_id,
                "target_id": target_id,
                "source_name": from_char.name,
                "target_name": to_char.name,
                "relation": rel.relation_type,
                "description": rel.description,
                "importance": min(1.0, importance)  # 确保不超过1.0
            })
            edge_id += 1
    
    # 如果关系数据不足，使用OpenAI补充分析
    if len(edges) < len(characters) * 0.5:  # 如果关系数少于角色数的一半，则需要额外分析
        logger.info("现有关系数据不足，使用OpenAI补充分析")
        
        # 获取小说内容
        content = novel_service.get_novel_chapters_content(db=db, novel_id=novel_id)
        if not content:
            raise ValueError("小说内容为空")
        
        try:
            # 构建角色列表作为提示
            character_names = [char.name for char in characters if char.importance and char.importance >= 2]
            # 限制角色数量以避免提示太长
            if len(character_names) > 20:
                character_names = character_names[:20]
            
            character_list = ", ".join(character_names)
            
            # 调用OpenAI API提取已知角色之间的关系
            extracted_relationships = await OpenAIClient.extract_character_relationships_from_list(
                content, character_list
            )
            
            # 合并提取的关系
            for rel in extracted_relationships.get("edges", []):
                source_name = rel.get("source_name")
                target_name = rel.get("target_name")
                
                if source_name in character_map and target_name in character_map:
                    # 检查是否已存在这对角色的关系
                    pair_exists = False
                    for existing_edge in edges:
                        if (existing_edge["source_name"] == source_name and existing_edge["target_name"] == target_name) or \
                           (existing_edge["source_name"] == target_name and existing_edge["target_name"] == source_name):
                            pair_exists = True
                            break
                    
                    if not pair_exists:
                        source_id = character_map[source_name]["id"]
                        target_id = character_map[target_name]["id"]
                        
                        edges.append({
                            "id": edge_id,
                            "source_id": source_id,
                            "target_id": target_id,
                            "source_name": source_name,
                            "target_name": target_name,
                            "relation": rel.get("relation", "关系未知"),
                            "description": rel.get("description", ""),
                            "importance": rel.get("importance", 0.5)
                        })
                        edge_id += 1
            
            # 添加关系到数据库
            for edge in edges:
                if edge.get("id") > len(existing_relationships):  # 只添加新的关系
                    source_char_id = character_map[edge["source_name"]]["character_id"]
                    target_char_id = character_map[edge["target_name"]]["character_id"]
                    
                    # 检查关系是否已存在
                    existing = db.query(novel.Relationship).filter(
                        novel.Relationship.novel_id == novel_id,
                        novel.Relationship.from_character_id == source_char_id,
                        novel.Relationship.to_character_id == target_char_id
                    ).first()
                    
                    if not existing:
                        new_relationship = novel.Relationship(
                            novel_id=novel_id,
                            from_character_id=source_char_id,
                            to_character_id=target_char_id,
                            relation_type=edge["relation"],
                            description=edge["description"]
                        )
                        db.add(new_relationship)
            
            db.commit()
            logger.info(f"添加了新的角色关系到数据库")
                
        except Exception as e:
            logger.error(f"使用OpenAI提取角色关系失败: {str(e)}")
            # 即使OpenAI分析失败，我们仍然返回已有的关系数据
    
    # 汇总关系图数据
    relationship_data = {
        "nodes": nodes,
        "edges": edges
    }
    
    # 如果指定了中心角色，过滤关系图
    if character_id:
        character = novel_service.get_character(db=db, character_id=character_id)
        if not character:
            raise ValueError("指定的角色不存在")
            
        # 过滤出与中心角色相关的节点和边
        filtered_data = filter_relationship_graph(
            graph_data=relationship_data,
            center_name=character.name,
            depth=depth
        )
        
        # 保存到数据库
        save_relationship_graph(db, novel_id, character_id, depth, filtered_data)
        
        return filtered_data
    
    # 保存到数据库
    save_relationship_graph(db, novel_id, None, depth, relationship_data)
    
    return relationship_data

def get_cached_relationship_graph(
    db: Session,
    novel_id: int,
    character_id: Optional[int] = None,
    depth: int = 1
) -> Optional[Dict[str, Any]]:
    """从数据库获取缓存的关系图数据
    
    Args:
        db: 数据库会话
        novel_id: 小说ID
        character_id: 可选的中心角色ID
        depth: 关系网络深度
        
    Returns:
        缓存的关系图数据，如果不存在则返回None
    """
    from app.models.novel import RelationshipGraph, RelationshipEdge
    
    logger.info(f"查询缓存: novel_id={novel_id}, character_id={character_id}, depth={depth}")
    
    # 查询条件
    query = db.query(RelationshipGraph).filter(
        RelationshipGraph.novel_id == novel_id,
        RelationshipGraph.depth == depth
    )
    
    if character_id:
        query = query.filter(RelationshipGraph.character_id == character_id)
    else:
        query = query.filter(RelationshipGraph.character_id == None)
    
    # 获取缓存的图
    cached_graph = query.first()
    
    if not cached_graph:
        return None
    
    # 获取边数据
    edges = db.query(RelationshipEdge).filter(
        RelationshipEdge.graph_id == cached_graph.id
    ).all()
    
    # 构建返回数据
    return {
        "nodes": cached_graph.nodes,
        "edges": [
            {
                "id": edge.id,
                "source_id": edge.source_id,
                "target_id": edge.target_id,
                "source_name": edge.source_name,
                "target_name": edge.target_name,
                "relation": edge.relation,
                "description": edge.description,
                "importance": edge.importance
            }
            for edge in edges
        ]
    }

def save_relationship_graph(
    db: Session,
    novel_id: int,
    character_id: Optional[int],
    depth: int,
    graph_data: Dict[str, Any]
) -> None:
    """保存关系图数据到数据库
    
    Args:
        db: 数据库会话
        novel_id: 小说ID
        character_id: 可选的中心角色ID
        depth: 关系网络深度
        graph_data: 关系图数据
    """
    from app.models.novel import RelationshipGraph, RelationshipEdge
    
    # 删除可能存在的旧数据
    query = db.query(RelationshipGraph).filter(
        RelationshipGraph.novel_id == novel_id,
        RelationshipGraph.depth == depth
    )
    
    if character_id:
        query = query.filter(RelationshipGraph.character_id == character_id)
    else:
        query = query.filter(RelationshipGraph.character_id == None)
    
    existing = query.first()
    if existing:
        db.delete(existing)
        db.flush()
    
    # 创建新的图数据
    new_graph = RelationshipGraph(
        novel_id=novel_id,
        character_id=character_id,
        depth=depth,
        nodes=graph_data["nodes"]
    )
    
    db.add(new_graph)
    db.flush()  # 刷新以获取新ID
    
    # 添加边数据
    for edge_data in graph_data["edges"]:
        edge = RelationshipEdge(
            graph_id=new_graph.id,
            source_id=edge_data["source_id"],
            target_id=edge_data["target_id"],
            source_name=edge_data["source_name"],
            target_name=edge_data["target_name"],
            relation=edge_data["relation"],
            description=edge_data.get("description"),
            importance=edge_data.get("importance", 1.0)
        )
        db.add(edge)
    
    db.commit()
    logger.info(f"保存关系图数据到数据库: novel_id={novel_id}, character_id={character_id}, depth={depth}")

def get_timeline(
    db: Session, 
    novel_id: int, 
    character_id: Optional[int] = None,
    start_chapter: Optional[int] = None,
    end_chapter: Optional[int] = None
) -> schemas.TimelineResponse:
    """获取时间线"""
    # 查询事件
    query = db.query(novel.Event).filter(novel.Event.novel_id == novel_id)
    
    if character_id:
        # 如果指定了角色，只获取该角色参与的事件
        # 通过EventParticipation表关联查询
        query = query.join(
            novel.EventParticipation,
            novel.Event.id == novel.EventParticipation.event_id
        ).filter(novel.EventParticipation.character_id == character_id)
    
    if start_chapter:
        query = query.filter(novel.Event.chapter_id >= start_chapter)
    
    if end_chapter:
        query = query.filter(novel.Event.chapter_id <= end_chapter)
    
    # 按章节顺序排序
    events = query.order_by(novel.Event.chapter_id).all()
    
    # 构建事件详情
    event_details = []
    for event in events:
        # 获取参与者
        participants = db.query(novel.EventParticipation).filter(
            novel.EventParticipation.event_id == event.id
        ).all()
        
        participant_details = []
        for p in participants:
            character = db.query(novel.Character).filter(
                novel.Character.id == p.character_id
            ).first()
            
            if character:
                participant_details.append({
                    "character_id": character.id,
                    "name": character.name,
                    "role": p.role
                })
        
        # 获取地点信息
        location = None
        if event.location_id:
            loc = db.query(novel.Location).filter(
                novel.Location.id == event.location_id
            ).first()
            
            if loc:
                location = {
                    "location_id": loc.id,
                    "name": loc.name,
                    "description": loc.description
                }
        
        event_details.append({
            "id": event.id,
            "novel_id": event.novel_id,
            "name": event.name,
            "description": event.description,
            "chapter_id": event.chapter_id,
            "location_id": event.location_id,
            "time_description": event.time_description,
            "importance": event.importance,
            "participants": participant_details,
            "location": location
        })
    
    return {
        "events": event_details
    }

def get_character_journey(db: Session, novel_id: int, character_id: int) -> Dict[str, Any]:
    """获取角色旅程"""
    # 获取角色信息
    character = db.query(novel.Character).filter(
        novel.Character.id == character_id,
        novel.Character.novel_id == novel_id
    ).first()
    
    if not character:
        raise ValueError("角色不存在")
    
    # 获取角色参与的事件（按时间顺序）
    events = db.query(novel.Event).join(
        novel.EventParticipation,
        novel.Event.id == novel.EventParticipation.event_id
    ).filter(
        novel.EventParticipation.character_id == character_id,
        novel.Event.novel_id == novel_id
    ).order_by(novel.Event.chapter_id).all()
    
    # 获取角色的关系
    relationships = []
    from_relationships = db.query(novel.Relationship).filter(
        novel.Relationship.from_character_id == character_id,
        novel.Relationship.novel_id == novel_id
    ).all()
    
    to_relationships = db.query(novel.Relationship).filter(
        novel.Relationship.to_character_id == character_id,
        novel.Relationship.novel_id == novel_id
    ).all()
    
    # 处理角色的关系
    for rel in from_relationships:
        other_character = db.query(novel.Character).filter(
            novel.Character.id == rel.to_character_id
        ).first()
        
        if other_character:
            relationships.append({
                "character_id": other_character.id,
                "name": other_character.name,
                "relation_type": rel.relation_type,
                "description": rel.description,
                "direction": "outgoing",
                "importance": other_character.importance or 1,
                "first_chapter": rel.first_chapter_id,
                "strength": 0.5 + (other_character.importance or 1) * 0.1  # 根据角色重要性计算关系强度
            })
    
    for rel in to_relationships:
        other_character = db.query(novel.Character).filter(
            novel.Character.id == rel.from_character_id
        ).first()
        
        if other_character:
            relationships.append({
                "character_id": other_character.id,
                "name": other_character.name,
                "relation_type": rel.relation_type,
                "description": rel.description,
                "direction": "incoming",
                "importance": other_character.importance or 1,
                "first_chapter": rel.first_chapter_id,
                "strength": 0.5 + (other_character.importance or 1) * 0.1  # 根据角色重要性计算关系强度
            })
    
    # 分析角色旅程的阶段
    stages = []
    
    if events:
        # 计算出场章节数量和相关事件数量
        chapters_involved = set()
        for event in events:
            if event.chapter_id:
                chapters_involved.add(event.chapter_id)
        
        # 将事件分段（根据事件的数量确定阶段数）
        stage_count = min(5, max(2, len(events) // 5))  # 至少2个阶段，最多5个阶段
        stage_size = max(1, len(events) // stage_count)
        
        # 生成各个阶段
        stage_names = ["初登场", "成长", "转折", "挑战", "高潮"]
        
        for i in range(0, min(stage_count, len(stage_names))):
            start_idx = i * stage_size
            end_idx = min(len(events), (i + 1) * stage_size - 1)
            
            if start_idx <= end_idx:
                stage_events = events[start_idx:end_idx+1]
                first_event = stage_events[0]
                last_event = stage_events[-1]
                
                # 计算阶段关键事件（重要性>=3的事件）
                key_events = [
                    {
                        "event_id": e.id,
                        "name": e.name,
                        "description": e.description,
                        "chapter_id": e.chapter_id,
                        "importance": e.importance,
                        "time_description": e.time_description
                    } for e in stage_events if e.importance >= 3
                ]
                
                # 如果没有重要事件，则选取最重要的一个事件
                if not key_events and stage_events:
                    most_important = max(stage_events, key=lambda e: e.importance)
                    key_events = [{
                        "event_id": most_important.id,
                        "name": most_important.name,
                        "description": most_important.description,
                        "chapter_id": most_important.chapter_id,
                        "importance": most_important.importance,
                        "time_description": most_important.time_description
                    }]
                
                stage = {
                    "name": stage_names[i],
                    "title": f"第{i+1}阶段: {stage_names[i]}",
                    "description": f"从「{first_event.name}」到「{last_event.name}」",
                    "start_chapter": first_event.chapter_id,
                    "end_chapter": last_event.chapter_id,
                    "key_events": key_events
                }
                stages.append(stage)
    
    # 生成情感变化分析
    emotions = []
    if events:
        # 简单模拟情感变化（实际项目可能需要NLP模型分析）
        # 这里我们根据事件重要性和描述简单生成
        chapter_emotions = {}
        
        for event in events:
            if event.chapter_id:
                emotion_value = min(10, max(0, 5 + (event.importance - 3) * 2))  # 1-5情绪值
                
                # 如果描述中有负面词，调整情绪值为负向
                negative_words = ['死亡', '失败', '悲伤', '愤怒', '失去', '背叛', '伤害']
                for word in negative_words:
                    if event.description and word in event.description:
                        emotion_value = max(0, emotion_value - 4)
                        break
                
                if event.chapter_id in chapter_emotions:
                    chapter_emotions[event.chapter_id].append(emotion_value)
                else:
                    chapter_emotions[event.chapter_id] = [emotion_value]
        
        # 对每个章节取平均情感值
        for chapter_id, values in sorted(chapter_emotions.items()):
            emotions.append({
                "chapter_id": chapter_id,
                "value": sum(values) / len(values)
            })
    
    # 计算统计数据
    stats = {
        "chapters_count": len(set(e.chapter_id for e in events if e.chapter_id)),
        "events_count": len(events),
        "relationships_count": len(relationships),
        "key_events_count": sum(len(stage["key_events"]) for stage in stages),
        "emotion_avg": round(sum(e["value"] for e in emotions) / len(emotions), 2) if emotions else 0
    }
    
    # 生成角色旅程总结（简单版）
    journey_summary = f"{character.name}的旅程共经历了{stats['chapters_count']}个章节，参与了{stats['events_count']}个事件，与{stats['relationships_count']}个角色建立了关系。"
    
    # 构建结果
    return {
        "character": {
            "id": character.id,
            "name": character.name,
            "description": character.description,
            "alias": character.alias,
            "first_appearance": character.first_appearance,
            "importance": character.importance
        },
        "journey": {
            "summary": journey_summary,
            "stages": stages,
            "events": [
                {
                    "event_id": e.id,
                    "name": e.name,
                    "description": e.description,
                    "chapter_id": e.chapter_id,
                    "importance": e.importance,
                    "time_description": e.time_description
                } for e in events
            ],
            "relationships": relationships
        },
        "emotions": emotions,
        "stats": stats,
        "stages": stages,
        "key_events": [e for stage in stages for e in stage["key_events"]]
    }

def get_item_lineage(db: Session, novel_id: int, item_id: int) -> Dict[str, Any]:
    """获取物品传承历史"""
    # 获取物品信息
    item = db.query(novel.Item).filter(
        novel.Item.id == item_id,
        novel.Item.novel_id == novel_id
    ).first()
    
    if not item:
        raise ValueError("物品不存在")
    
    # 获取物品转移记录
    transfers = db.query(novel.ItemTransfer).filter(
        novel.ItemTransfer.item_id == item_id
    ).order_by(novel.ItemTransfer.chapter_id).all()
    
    # 构建拥有者历史
    owners_history = []
    for transfer in transfers:
        from_character = None
        if transfer.from_character_id:
            from_char = db.query(novel.Character).filter(
                novel.Character.id == transfer.from_character_id
            ).first()
            if from_char:
                from_character = {
                    "id": from_char.id,
                    "name": from_char.name
                }
        
        to_character = None
        if transfer.to_character_id:
            to_char = db.query(novel.Character).filter(
                novel.Character.id == transfer.to_character_id
            ).first()
            if to_char:
                to_character = {
                    "id": to_char.id,
                    "name": to_char.name
                }
        
        chapter = None
        if transfer.chapter_id:
            chap = db.query(novel.Chapter).filter(
                novel.Chapter.id == transfer.chapter_id
            ).first()
            if chap:
                chapter = {
                    "id": chap.id,
                    "title": chap.title,
                    "number": chap.number
                }
        
        owners_history.append({
            "from_character": from_character,
            "to_character": to_character,
            "chapter": chapter,
            "description": transfer.description
        })
    
    # 获取当前拥有者
    current_owner = None
    if item.owner_id:
        owner = db.query(novel.Character).filter(
            novel.Character.id == item.owner_id
        ).first()
        
        if owner:
            current_owner = {
                "id": owner.id,
                "name": owner.name,
                "description": owner.description
            }
    
    # 构建结果
    return {
        "item": {
            "id": item.id,
            "name": item.name,
            "description": item.description
        },
        "current_owner": current_owner,
        "ownership_history": owners_history
    }

def get_location_events(db: Session, novel_id: int, location_id: int) -> Dict[str, Any]:
    """获取地点相关事件"""
    # 获取地点信息
    location = db.query(novel.Location).filter(
        novel.Location.id == location_id,
        novel.Location.novel_id == novel_id
    ).first()
    
    if not location:
        raise ValueError("地点不存在")
    
    # 获取该地点发生的事件
    events = db.query(novel.Event).filter(
        novel.Event.location_id == location_id,
        novel.Event.novel_id == novel_id
    ).order_by(novel.Event.chapter_id).all()
    
    # 获取该地点出现的角色（通过事件参与关系）
    character_ids = set()
    event_participation = db.query(novel.EventParticipation).filter(
        novel.EventParticipation.event_id.in_([e.id for e in events])
    ).all()
    
    for participation in event_participation:
        character_ids.add(participation.character_id)
    
    characters = db.query(novel.Character).filter(
        novel.Character.id.in_(character_ids)
    ).all()
    
    character_counts = {}
    for participation in event_participation:
        character_counts[participation.character_id] = character_counts.get(participation.character_id, 0) + 1
    
    character_details = []
    for character in characters:
        character_details.append({
            "id": character.id,
            "name": character.name,
            "count": character_counts.get(character.id, 0)
        })
    
    # 按出现次数排序
    character_details.sort(key=lambda x: x["count"], reverse=True)
    
    # 构建事件时间线
    event_timeline = []
    for event in events:
        participants = db.query(novel.EventParticipation).filter(
            novel.EventParticipation.event_id == event.id
        ).all()
        
        participant_details = []
        for p in participants:
            character = next((c for c in characters if c.id == p.character_id), None)
            if character:
                participant_details.append({
                    "id": character.id,
                    "name": character.name,
                    "role": p.role
                })
        
        chapter = None
        if event.chapter_id:
            chap = db.query(novel.Chapter).filter(
                novel.Chapter.id == event.chapter_id
            ).first()
            if chap:
                chapter = {
                    "id": chap.id,
                    "title": chap.title,
                    "number": chap.number
                }
        
        event_timeline.append({
            "id": event.id,
            "name": event.name,
            "description": event.description,
            "importance": event.importance,
            "time_description": event.time_description,
            "chapter": chapter,
            "participants": participant_details
        })
    
    # 构建结果
    return {
        "location": {
            "id": location.id,
            "name": location.name,
            "description": location.description,
            "parent_id": location.parent_id
        },
        "events": event_timeline,
        "characters": character_details,
    }

def filter_relationship_graph(
    graph_data: Dict[str, Any],
    center_name: str,
    depth: int = 2
) -> Dict[str, Any]:
    """根据中心角色和深度过滤关系图
    
    Args:
        graph_data: 原始关系图数据
        center_name: 中心角色名称
        depth: 关系网络深度
        
    Returns:
        过滤后的关系图数据
    """
    # 首先找到中心角色的节点ID
    center_id = None
    for node in graph_data["nodes"]:
        if node["name"] == center_name:
            center_id = node["id"]
            break
    
    if not center_id:
        return graph_data  # 如果找不到中心角色，返回原始数据
    
    # 使用BFS找到指定深度内的所有相关节点
    related_nodes = {center_id}
    current_depth = 0
    current_layer = {center_id}
    
    while current_depth < depth and current_layer:
        next_layer = set()
        for edge in graph_data["edges"]:
            if edge["source_id"] in current_layer:
                next_layer.add(edge["target_id"])
            if edge["target_id"] in current_layer:
                next_layer.add(edge["source_id"])
        
        current_layer = next_layer - related_nodes
        related_nodes.update(current_layer)
        current_depth += 1
    
    # 过滤节点
    filtered_nodes = [
        node for node in graph_data["nodes"]
        if node["id"] in related_nodes
    ]
    
    # 过滤边
    filtered_edges = [
        edge for edge in graph_data["edges"]
        if edge["source_id"] in related_nodes and edge["target_id"] in related_nodes
    ]
    
    return {
        "nodes": filtered_nodes,
        "edges": filtered_edges
    } 