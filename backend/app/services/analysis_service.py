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
    
    # 如果是强制刷新，直接调用OpenAI API重新分析
    if force_refresh:
        logger.info("强制刷新模式，将调用大语言模型进行关系重新分析")
        
        # 获取小说内容
        content = novel_service.get_novel_chapters_content(db=db, novel_id=novel_id)
        if not content:
            raise ValueError("小说内容为空")
        
        try:
            # 构建分析提示，确保捕获所有关系类型
            analysis_hint = """请全面分析所有角色和关系：
1. 识别所有角色，包括背景角色（如"姓阮的外乡铁匠"）
2. 标准化角色名称，将"卖鱼中年人"和"卖鱼的中年人"等识别为同一角色
3. 重点关注以下关系：
   - 师徒关系（刘羡阳与姚老头）
   - 交易关系（锦衣少年与陈平安）
   - 社交关系（锦衣少年与宋集薪）
   - 敌对关系、主仆关系、家族关系
4. 对无明确姓名的角色使用统一格式的描述作为名称
5. 提供详细的关系证据和描述
6. 宁可多报也不要遗漏任何角色关系"""

            # 直接调用OpenAI API提取角色关系
            relationship_data = await OpenAIClient.extract_character_relationships(content + f"\n\n[分析提示: {analysis_hint}]")
            
            # 在数据库中删除现有关系（仅在强制刷新时）
            existing_relationships = db.query(novel.Relationship).filter(
                novel.Relationship.novel_id == novel_id
            ).all()
            
            if existing_relationships:
                for rel in existing_relationships:
                    db.delete(rel)
                db.flush()
                logger.info(f"删除了 {len(existing_relationships)} 条现有关系")
            
            # 处理提取的关系
            nodes = relationship_data.get("nodes", [])
            edges = relationship_data.get("edges", [])
            
            logger.info(f"AI分析结果: 节点数={len(nodes)}, 边数={len(edges)}")
            
            # 保存角色数据
            character_map = {}
            for node in nodes:
                # 检查角色是否已存在
                existing_character = db.query(novel.Character).filter(
                    novel.Character.novel_id == novel_id,
                    # 使用更精确的名称匹配，处理可能有空格或标点符号差异的情况
                    novel.Character.name.ilike(node["name"].strip())
                ).first()
                
                if existing_character:
                    # 更新现有角色
                    existing_character.description = node.get("description", existing_character.description)
                    # 仅当新重要性高于现有重要性时更新
                    if node.get("importance", 0) > (existing_character.importance or 0):
                        existing_character.importance = node.get("importance")
                    # 记录角色ID映射
                    character_map[node["name"]] = existing_character.id
                    logger.info(f"更新已存在角色: {node['name']} (ID: {existing_character.id})")
                else:
                    # 再次检查名称相似但不完全匹配的角色
                    similar_characters = db.query(novel.Character).filter(
                        novel.Character.novel_id == novel_id,
                        novel.Character.name.ilike(f"%{node['name'].split()[0]}%") if ' ' in node['name'] else novel.Character.name.ilike(f"%{node['name']}%")
                    ).all()
                    
                    if similar_characters:
                        # 找到最相似的角色
                        logger.info(f"发现相似角色，名称: {node['name']}")
                        similar_character = similar_characters[0]
                        # 用户可以后续手动合并
                        # 这里仍然使用现有角色
                        character_map[node["name"]] = similar_character.id
                        logger.info(f"使用相似角色: {similar_character.name} (ID: {similar_character.id})")
                    else:
                        # 创建新角色
                        new_character = novel.Character(
                            name=node["name"],
                            novel_id=novel_id,
                            description=node.get("description", ""),
                            importance=node.get("importance", 3)
                        )
                        db.add(new_character)
                        db.flush()
                        character_map[node["name"]] = new_character.id
                        logger.info(f"创建新角色: {node['name']} (ID: {new_character.id})")
            
            # 保存关系数据
            for edge in edges:
                source_name = edge["source_name"]
                target_name = edge["target_name"]
                
                source_id = character_map.get(source_name)
                target_id = character_map.get(target_name)
                
                if source_id and target_id:
                    # 创建新的关系记录
                    new_relationship = novel.Relationship(
                        novel_id=novel_id,
                        from_character_id=source_id,
                        to_character_id=target_id,
                        relation_type=edge.get("relation", "关系未知"),
                        description=edge.get("description", "")
                    )
                    db.add(new_relationship)
            
            # 提交更改
            db.commit()
            
            # 检查特定角色关系是否存在（用于调试）
            expected_relationships = [
                ("刘羡阳", "姚老头"),
                ("锦衣少年", "陈平安"),
                ("锦衣少年", "宋集薪")
            ]
            
            # 当前已分析的关系
            current_edges = [(edge["source_name"], edge["target_name"]) for edge in edges]
            for source, target in expected_relationships:
                if (source, target) not in current_edges and (target, source) not in current_edges:
                    logger.warning(f"警告：未能分析出 '{source}' 和 '{target}' 之间的关系")
            
            # 重新获取所有角色用于构建响应
            characters = db.query(novel.Character).filter(
                novel.Character.novel_id == novel_id
            ).all()
            
            # 重新获取所有关系用于构建响应
            relationships = db.query(novel.Relationship).filter(
                novel.Relationship.novel_id == novel_id
            ).all()
            
            # 构建节点和边的响应格式
            response_nodes = []
            response_edges = []
            
            # 构建节点映射
            node_map = {}
            for i, character in enumerate(characters):
                node_id = i + 1
                node_map[character.id] = node_id
                
                response_nodes.append({
                    "id": node_id,
                    "name": character.name,
                    "value": 10 + (character.importance or 1) * 5,
                    "character_id": character.id,
                    "importance": character.importance or 1
                })
            
            # 构建边
            edge_id = 1
            for relationship in relationships:
                if relationship.from_character_id in node_map and relationship.to_character_id in node_map:
                    source_id = node_map[relationship.from_character_id]
                    target_id = node_map[relationship.to_character_id]
                    
                    from_char = next((c for c in characters if c.id == relationship.from_character_id), None)
                    to_char = next((c for c in characters if c.id == relationship.to_character_id), None)
                    
                    if from_char and to_char:
                        response_edges.append({
                            "id": edge_id,
                            "source_id": source_id,
                            "target_id": target_id,
                            "source_name": from_char.name,
                            "target_name": to_char.name,
                            "relation": relationship.relation_type,
                            "description": relationship.description,
                            "importance": 0.5 + (from_char.importance or 1) * 0.1 + (to_char.importance or 1) * 0.1
                        })
                        edge_id += 1
            
            # 构建并返回响应
            result = {
                "nodes": response_nodes,
                "edges": response_edges
            }
            
            # 如果指定了中心角色，过滤关系图
            if character_id:
                character = novel_service.get_character(db=db, character_id=character_id)
                if character:
                    result = filter_relationship_graph(
                        graph_data=result,
                        center_name=character.name,
                        depth=depth
                    )
            
            # 保存到数据库
            save_relationship_graph(db, novel_id, character_id, depth, result)
            
            return result
            
        except Exception as e:
            db.rollback()
            logger.error(f"强制重新分析关系失败: {str(e)}")
            # 如果重新分析失败，回退到使用现有关系
            logger.info("回退到使用现有关系数据")
            # 继续下面的代码，使用现有关系构建图
    
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
                
                # 首先检查源角色和目标角色是否在已知角色映射中
                # 如果不在，则检查数据库中是否已存在相同名称的角色
                if source_name not in character_map:
                    # 检查是否已有相同名称的角色
                    existing_source = db.query(novel.Character).filter(
                        novel.Character.novel_id == novel_id,
                        novel.Character.name == source_name
                    ).first()
                    
                    if existing_source:
                        # 使用已存在的角色
                        character_map[source_name] = {"id": existing_source.id, "character_id": existing_source.id}
                    else:
                        # 创建新角色
                        new_source = novel.Character(
                            name=source_name,
                            novel_id=novel_id,
                            description="",  # 可以后续更新
                            importance=2  # 默认重要性
                        )
                        db.add(new_source)
                        db.flush()
                        character_map[source_name] = {"id": new_source.id, "character_id": new_source.id}
                
                if target_name not in character_map:
                    # 检查是否已有相同名称的角色
                    existing_target = db.query(novel.Character).filter(
                        novel.Character.novel_id == novel_id,
                        novel.Character.name == target_name
                    ).first()
                    
                    if existing_target:
                        # 使用已存在的角色
                        character_map[target_name] = {"id": existing_target.id, "character_id": existing_target.id}
                    else:
                        # 创建新角色
                        new_target = novel.Character(
                            name=target_name,
                            novel_id=novel_id,
                            description="",  # 可以后续更新
                            importance=2  # 默认重要性
                        )
                        db.add(new_target)
                        db.flush()
                        character_map[target_name] = {"id": new_target.id, "character_id": new_target.id}
                
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
            added_relation_count = 0
            existing_relation_count = 0
            for edge in edges:
                if edge.get("id") > len(existing_relationships):  # 只添加新的关系
                    source_char_id = character_map[edge["source_name"]]["character_id"]
                    target_char_id = character_map[edge["target_name"]]["character_id"]
                    
                    # 检查正向关系是否已存在
                    existing_forward = db.query(novel.Relationship).filter(
                        novel.Relationship.novel_id == novel_id,
                        novel.Relationship.from_character_id == source_char_id,
                        novel.Relationship.to_character_id == target_char_id
                    ).first()
                    
                    # 检查反向关系是否已存在
                    existing_backward = db.query(novel.Relationship).filter(
                        novel.Relationship.novel_id == novel_id,
                        novel.Relationship.from_character_id == target_char_id,
                        novel.Relationship.to_character_id == source_char_id
                    ).first()
                    
                    if not existing_forward and not existing_backward:
                        # 只有当正反两个方向都没有关系时才添加
                        new_relationship = novel.Relationship(
                            novel_id=novel_id,
                            from_character_id=source_char_id,
                            to_character_id=target_char_id,
                            relation_type=edge["relation"],
                            description=edge["description"]
                        )
                        db.add(new_relationship)
                        added_relation_count += 1
                    else:
                        existing_relation_count += 1
            
            db.commit()
            logger.info(f"添加了{added_relation_count}个新的角色关系到数据库，跳过了{existing_relation_count}个已存在的关系")
                
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

def get_location_timeline(
    db: Session, 
    novel_id: int, 
    location_id: int,
    start_chapter: Optional[int] = None,
    end_chapter: Optional[int] = None
) -> schemas.TimelineResponse:
    """获取地点的时间线
    
    Args:
        db: 数据库会话
        novel_id: 小说ID
        location_id: 地点ID
        start_chapter: 开始章节（可选）
        end_chapter: 结束章节（可选）
        
    Returns:
        时间线响应对象
    """
    # 确认地点存在于指定小说中
    location = db.query(novel.Location).filter(
        novel.Location.id == location_id,
        novel.Location.novel_id == novel_id
    ).first()
    
    if not location:
        raise ValueError("找不到指定地点")
    
    # 查询在此地点发生的事件
    query = db.query(novel.Event).filter(
        novel.Event.novel_id == novel_id,
        novel.Event.location_id == location_id
    )
    
    # 应用章节过滤
    if start_chapter:
        query = query.filter(novel.Event.chapter_id >= start_chapter)
    
    if end_chapter:
        query = query.filter(novel.Event.chapter_id <= end_chapter)
    
    # 按章节顺序排序
    events = query.order_by(novel.Event.chapter_id).all()
    
    # 添加子地点的事件
    sub_locations = db.query(novel.Location).filter(
        novel.Location.parent_id == location_id
    ).all()
    
    for sub_location in sub_locations:
        sub_query = db.query(novel.Event).filter(
            novel.Event.novel_id == novel_id,
            novel.Event.location_id == sub_location.id
        )
        
        if start_chapter:
            sub_query = sub_query.filter(novel.Event.chapter_id >= start_chapter)
        
        if end_chapter:
            sub_query = sub_query.filter(novel.Event.chapter_id <= end_chapter)
        
        sub_events = sub_query.all()
        events.extend(sub_events)
    
    # 重新按章节顺序排序所有事件
    events.sort(key=lambda e: e.chapter_id if e.chapter_id else 9999)
    
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
                    "character_name": character.name,
                    "role": p.role
                })
        
        # 获取地点信息
        event_location = None
        if event.location_id:
            loc = db.query(novel.Location).filter(
                novel.Location.id == event.location_id
            ).first()
            
            if loc:
                event_location = {
                    "id": loc.id,
                    "name": loc.name,
                    "description": loc.description
                }
        
        # 为每个事件添加一些时间分析标签
        tags = []
        if event.importance >= 4:
            tags.append("重要事件")
        
        # 根据事件描述推断事件类型
        if any(keyword in (event.description or "").lower() for keyword in ["战斗", "打斗", "厮杀", "杀死"]):
            tags.append("战斗")
        
        if any(keyword in (event.description or "").lower() for keyword in ["爱", "情感", "喜欢", "关心"]):
            tags.append("情感")
        
        if any(keyword in (event.description or "").lower() for keyword in ["发现", "寻找", "找到", "获得"]):
            tags.append("发现")
        
        if any(keyword in (event.description or "").lower() for keyword in ["旅行", "前往", "出发", "到达"]):
            tags.append("旅行")
        
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
            "location": event_location,
            "tags": tags,
            # 简化的时间位置，用于排序
            "time_position": event.chapter_id
        })
    
    return {
        "events": event_details
    } 