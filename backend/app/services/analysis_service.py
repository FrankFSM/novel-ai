from sqlalchemy.orm import Session
from typing import Dict, List, Any, Optional
import logging
import networkx as nx

from app.models import novel, schemas

logger = logging.getLogger(__name__)

def get_relationship_graph(
    db: Session, 
    novel_id: int, 
    character_id: Optional[int] = None,
    depth: int = 1
) -> schemas.RelationshipGraphResponse:
    """获取关系网络图"""
    # 创建一个图
    G = nx.Graph()
    
    # 查询关系
    query = db.query(novel.Relationship).filter(novel.Relationship.novel_id == novel_id)
    
    if character_id:
        # 如果指定了角色，只获取与该角色相关的关系
        query = query.filter(
            (novel.Relationship.from_character_id == character_id) | 
            (novel.Relationship.to_character_id == character_id)
        )
    
    relationships = query.all()
    
    # 角色ID集合，用于获取角色信息
    character_ids = set()
    
    # 添加节点和边
    for rel in relationships:
        character_ids.add(rel.from_character_id)
        character_ids.add(rel.to_character_id)
        
        # 添加边，带上关系类型
        G.add_edge(
            rel.from_character_id, 
            rel.to_character_id, 
            type=rel.relation_type, 
            desc=rel.description
        )
    
    # 如果需要扩展深度
    if depth > 1 and character_id:
        current_nodes = set(G.nodes())
        for _ in range(depth - 1):
            new_nodes = set()
            for node in current_nodes:
                # 查询与当前节点相关的其他关系
                relations = db.query(novel.Relationship).filter(
                    novel.Relationship.novel_id == novel_id,
                    ((novel.Relationship.from_character_id == node) |
                     (novel.Relationship.to_character_id == node)),
                    ~((novel.Relationship.from_character_id.in_(character_ids)) &
                      (novel.Relationship.to_character_id.in_(character_ids)))
                ).all()
                
                for rel in relations:
                    character_ids.add(rel.from_character_id)
                    character_ids.add(rel.to_character_id)
                    if rel.from_character_id not in G.nodes():
                        new_nodes.add(rel.from_character_id)
                    if rel.to_character_id not in G.nodes():
                        new_nodes.add(rel.to_character_id)
                    G.add_edge(
                        rel.from_character_id, 
                        rel.to_character_id, 
                        type=rel.relation_type, 
                        desc=rel.description
                    )
            current_nodes = new_nodes
            if not current_nodes:
                break
    
    # 获取角色信息
    characters = db.query(novel.Character).filter(
        novel.Character.id.in_(character_ids)
    ).all()
    
    # 角色信息字典，用于构建结果
    character_dict = {c.id: c for c in characters}
    
    # 构建节点列表
    nodes = []
    for char_id in G.nodes():
        char = character_dict.get(char_id)
        if char:
            nodes.append({
                "id": char.id,
                "name": char.name,
                "description": char.description,
                "alias": char.alias
            })
    
    # 构建边列表
    edges = []
    for from_id, to_id, data in G.edges(data=True):
        edges.append({
            "source": from_id,
            "target": to_id,
            "type": data.get("type"),
            "description": data.get("desc")
        })
    
    return {
        "nodes": nodes,
        "edges": edges
    }

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
                "direction": "outgoing"
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
                "direction": "incoming"
            })
    
    # 分析角色旅程的阶段（简化版）
    stages = []
    current_stage = None
    
    if events:
        # 简单地以每10个事件为一个阶段
        stage_size = max(1, len(events) // 5)  # 最多5个阶段
        
        for i in range(0, len(events), stage_size):
            stage_events = events[i:i+stage_size]
            if stage_events:
                first_event = stage_events[0]
                last_event = stage_events[-1]
                
                stage = {
                    "title": f"第{len(stages)+1}阶段",
                    "description": f"从「{first_event.name}」到「{last_event.name}」",
                    "start_chapter": first_event.chapter_id,
                    "end_chapter": last_event.chapter_id,
                    "key_events": [
                        {
                            "event_id": e.id,
                            "name": e.name,
                            "description": e.description,
                            "chapter_id": e.chapter_id,
                            "importance": e.importance
                        } for e in stage_events if e.importance >= 3  # 只包括重要事件
                    ]
                }
                stages.append(stage)
    
    # 构建结果
    return {
        "character": {
            "id": character.id,
            "name": character.name,
            "description": character.description,
            "alias": character.alias,
            "first_appearance": character.first_appearance
        },
        "journey": {
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
        }
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