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
    
    character_info = [
        {
            "id": char.id,
            "name": char.name,
            "description": char.description,
            "importance": char.importance or 1
        }
        for char in characters
    ]
    
    # 4. 获取小说地点
    locations = db.query(novel.Location).filter(novel.Location.novel_id == novel_id).all()
    if not locations:
        logger.warning(f"小说ID {novel_id} 没有地点数据，无法关联事件与地点")
        return []
    
    location_info = [
        {
            "id": loc.id,
            "name": loc.name,
            "description": loc.description,
            "importance": loc.importance or 1
        }
        for loc in locations
    ]
    
    # 5. 使用OpenAI分析小说内容，提取事件
    try:
        # 清除现有事件数据
        db.query(novel.EventParticipation).filter(
            novel.EventParticipation.event_id.in_(
                db.query(novel.Event.id).filter(novel.Event.novel_id == novel_id)
            )
        ).delete(synchronize_session=False)
        
        db.query(novel.Event).filter(novel.Event.novel_id == novel_id).delete()
        db.commit()
        
        # 调用OpenAI API分析事件
        events = await extract_events_from_novel(
            novel_title=novel_obj.title,
            content=content[:15000],  # 限制内容长度，避免超出token限制
            characters=character_info,
            locations=location_info
        )
        
        if not events:
            logger.warning(f"AI分析未发现任何事件，将生成示例事件")
            # 如果AI分析失败，使用示例事件
            events = generate_sample_events(characters, locations)
        
        # 将事件保存到数据库
        for event_data in events:
            # 从事件数据中提取参与者信息
            participants = event_data.pop("participants", [])
            
            # 获取事件关联的地点ID
            location_id = None
            location_name = event_data.pop("location_name", None)
            if location_name:
                # 尝试通过名称查找地点
                location_obj = next((loc for loc in locations if loc.name == location_name), None)
                if location_obj:
                    location_id = location_obj.id
                else:
                    # 如果找不到匹配的地点，使用第一个地点
                    location_id = locations[0].id if locations else None
            else:
                # 直接使用第一个地点
                location_id = locations[0].id if locations else None
            
            # 创建事件
            new_event = novel.Event(
                novel_id=novel_id,
                location_id=location_id,
                **{k: v for k, v in event_data.items() if k in [
                    "name", "description", "chapter_id", "time_description", "importance"
                ] and v is not None}
            )
            db.add(new_event)
            db.flush()  # 获取新创建事件的ID
            
            # 添加事件参与者
            for participant in participants:
                character_name = participant.get("name")
                if not character_name:
                    continue
                    
                # 尝试通过名称查找角色
                character_obj = next((char for char in characters if char.name == character_name), None)
                if not character_obj:
                    # 如果找不到匹配的角色，跳过
                    continue
                    
                event_participation = novel.EventParticipation(
                    event_id=new_event.id,
                    character_id=character_obj.id,
                    role=participant.get("role", "参与者")
                )
                db.add(event_participation)
        
        db.commit()
        logger.info(f"成功为小说ID {novel_id} 添加了 {len(events)} 个事件")
        
        # 返回新创建的事件列表
        return events
        
    except Exception as e:
        db.rollback()
        logger.error(f"分析小说事件失败: {str(e)}")
        raise ValueError(f"分析小说事件失败: {str(e)}")

async def extract_events_from_novel(
    novel_title: str,
    content: str,
    characters: List[Dict[str, Any]],
    locations: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    使用OpenAI API从小说内容中提取事件
    
    Args:
        novel_title: 小说标题
        content: 小说内容
        characters: 角色信息列表
        locations: 地点信息列表
        
    Returns:
        List[Dict[str, Any]]: 事件列表
    """
    try:
        # 保护所有字符串免受%格式化问题的影响
        safe_novel_title = novel_title.replace("%", "%%") if novel_title else ""
        safe_content = content.replace("%", "%%") if content else ""
        
        # 构建提示，包含小说信息、角色和地点数据
        characters_text = ""
        try:
            characters_text = "\n".join([
                f"- {char['name'].replace('%', '%%')}: {(char['description'] or '无描述').replace('%', '%%')}" 
                for char in characters[:10]  # 限制角色数量，避免提示过长
            ])
        except Exception as e:
            logger.error(f"处理角色数据时出错: {e}")
            characters_text = "- 无角色数据"
        
        locations_text = ""
        try:
            locations_text = "\n".join([
                f"- {loc['name'].replace('%', '%%')}: {(loc['description'] or '无描述').replace('%', '%%')}" 
                for loc in locations[:10]  # 限制地点数量，避免提示过长
            ])
        except Exception as e:
            logger.error(f"处理地点数据时出错: {e}")
            locations_text = "- 无地点数据"
        
        # 构建提示模板，避免在f-string中直接使用可能包含%的变量
        prompt_template = """
        您是一位文学分析专家，擅长分析小说中的重要事件和情节。请分析以下小说内容，提取出关键事件。

        小说标题: {title}
        
        小说中的主要角色:
        {characters}
        
        小说中的主要地点:
        {locations}
        
        请根据以下小说内容，分析并提取出5-10个重要事件。对于每个事件，请提供：
        1. 事件名称
        2. 事件描述
        3. 事件发生的章节编号（如有）
        4. 事件的时间描述
        5. 事件的重要性评分（1-5，5为最重要）
        6. 事件发生的地点名称（从上述地点列表中选择）
        7. 参与事件的角色及其在事件中的角色（从上述角色列表中选择）
        
        小说内容片段如下:
        ```
        {content}
        ```
        
        请以JSON格式返回分析结果，格式如下:
        ```json
        [
          {{
            "name": "事件名称",
            "description": "事件描述",
            "chapter_id": 章节编号,
            "time_description": "时间描述",
            "importance": 重要性评分,
            "location_name": "地点名称",
            "participants": [
              {{
                "name": "角色名称",
                "role": "在事件中的角色"
              }}
            ]
          }}
        ]
        ```
        
        只返回JSON数据，不要有任何其他文本。确保JSON格式正确，可以被解析。
        """
        
        # 安全地填充模板
        safe_content_preview = safe_content[:12000] if safe_content else ""
        prompt = prompt_template.format(
            title=safe_novel_title,
            characters=characters_text,
            locations=locations_text,
            content=safe_content_preview
        )
        
        # 调用OpenAI API
        openai_client = OpenAIClient()
        response = await openai_client.chat_completion(
            messages=[
                {"role": "system", "content": "你是一个小说分析助手，擅长分析小说中的事件和情节。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        # 解析响应
        if not response or "choices" not in response:
            logger.error("OpenAI API返回无效响应")
            return []
            
        content = response["choices"][0]["message"]["content"]
        
        # 提取JSON部分
        import re
        import json
        
        try:
            # 尝试找到并提取JSON部分
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if json_match:
                json_str = json_match.group(1)
                logger.info("成功找到JSON代码块")
            else:
                # 如果没有找到```json标记，尝试直接解析整个内容
                json_str = content
                logger.info("未找到JSON代码块，尝试直接解析整个内容")
            
            # 清理并解析JSON
            json_str = OpenAIClient.clean_json_content(json_str)
            events = json.loads(json_str)
            
            if not isinstance(events, list):
                logger.error("解析的事件不是列表: %r", events)
                return []
                
            logger.info("成功从AI分析中提取了 %d 个事件", len(events))
            return events
        except Exception as json_error:
            logger.error("解析JSON响应时出错: %s", str(json_error))
            return []
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error("从小说内容中提取事件失败: %s", str(e))
        logger.error("错误详情: %s", error_trace)
        logger.error("尝试使用备用方法生成事件")
        return []

def generate_sample_events(characters, locations) -> List[Dict[str, Any]]:
    """
    生成示例事件（当AI分析失败时使用）
    
    Args:
        characters: 角色列表
        locations: 地点列表
        
    Returns:
        List[Dict[str, Any]]: 示例事件列表
    """
    try:
        sample_events = [
            {
                "name": "故事开始",
                "description": "主角登场并介绍了背景设定",
                "chapter_id": 1,
                "time_description": "故事伊始",
                "importance": 5,
                "location_name": locations[0].name if locations and hasattr(locations[0], 'name') else None,
                "participants": [
                    {"name": characters[0].name, "role": "主角"} if characters and hasattr(characters[0], 'name') else {"name": "未知角色", "role": "主角"}
                ]
            },
            {
                "name": "关键冲突",
                "description": "主角遇到了重大挑战",
                "chapter_id": 3,
                "time_description": "故事中期",
                "importance": 4,
                "location_name": (locations[1].name if len(locations) > 1 else (locations[0].name if locations else None)) if locations and hasattr(locations[0], 'name') else None,
                "participants": [
                    {"name": characters[0].name, "role": "挑战者"} if characters and hasattr(characters[0], 'name') else {"name": "未知角色", "role": "挑战者"},
                    {"name": characters[1].name, "role": "对手"} if len(characters) > 1 and hasattr(characters[1], 'name') else {"name": "未知对手", "role": "对手"}
                ]
            }
        ]
        logger.info("成功生成示例事件数据")
        return sample_events
    except Exception as e:
        logger.error("生成示例事件时出错: %s", str(e))
        # 返回最简单的备用数据
        return [
            {
                "name": "示例事件",
                "description": "这是一个自动生成的示例事件",
                "chapter_id": 1,
                "time_description": "未知",
                "importance": 3,
                "location_name": None,
                "participants": [{"name": "未知角色", "role": "角色"}]
            }
        ]

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
    try:
        # 获取事件
        event = db.query(novel.Event).filter(novel.Event.id == event_id).first()
        if not event:
            raise ValueError("事件不存在")
        
        # 获取小说
        novel_obj = db.query(novel.Novel).filter(novel.Novel.id == event.novel_id).first()
        if not novel_obj:
            raise ValueError("小说不存在")
        
        # 获取事件的地点信息
        location = None
        if event.location_id:
            location_obj = db.query(novel.Location).filter(novel.Location.id == event.location_id).first()
            if location_obj:
                location = location_obj.name
        
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
                    "name": character.name,
                    "role": participation.role
                })
        
        # 获取相关的章节内容
        context = ""
        if event.chapter_id:
            chapter = db.query(novel.Chapter).filter(
                novel.Chapter.id == event.chapter_id
            ).first()
            
            if chapter:
                context = chapter.content[:5000]  # 限制内容长度
        
        # 处理所有字符串确保安全
        safe_title = novel_obj.title.replace("%", "%%") if novel_obj.title else ""
        safe_event_name = event.name.replace("%", "%%") if event.name else ""
        safe_event_desc = (event.description or "无描述").replace("%", "%%")
        safe_time_desc = (event.time_description or "未知").replace("%", "%%")
        safe_location = (location or "未知").replace("%", "%%")
        safe_context = context.replace("%", "%%") if context else ""
        
        # 构建参与者文本，确保安全处理
        try:
            participants_text = ", ".join([
                f"{p['name'].replace('%', '%%')}（{p['role'].replace('%', '%%')}）" 
                for p in participants
            ]) if participants else "未知"
        except Exception as e:
            logger.error(f"处理参与者数据时出错: {e}")
            participants_text = "未知"
        
        # 构建提示模板
        prompt_template = """
        您是一位文学分析专家，擅长分析小说事件的重要性和影响。请分析以下事件的重要性、意义和对故事情节的影响。

        小说标题: {title}
        事件名称: {event_name}
        事件描述: {event_desc}
        发生章节: {chapter_id}
        时间描述: {time_desc}
        发生地点: {location}
        参与角色: {participants}

        相关内容片段:
        ```
        {context}
        ```

        请详细分析并回答以下问题:
        1. 这个事件在故事中的重要性维度有哪些？（列出3-5个关键词，如"关键转折点"、"角色发展"等）
        2. 这个事件对故事情节有哪些具体影响？（分析3-5个方面）
        3. 这个事件对角色发展有什么影响？
        4. 总体而言，这个事件在整个故事中的重要程度如何？

        请以JSON格式返回分析结果:
        ```json
        {{
          "name": "事件名称",
          "significance": ["重要性维度1", "重要性维度2", "重要性维度3"],
          "impact": [
            {{
              "aspect": "影响方面1",
              "description": "详细描述",
              "evidence": "证据或例子"
            }},
            {{
              "aspect": "影响方面2",
              "description": "详细描述",
              "evidence": "证据或例子"
            }}
          ],
          "analysis": "总体分析概述"
        }}
        ```

        只返回JSON数据，不要有任何其他文本。确保JSON格式正确，可以被解析。
        """
        
        # 安全地填充模板
        prompt = prompt_template.format(
            title=safe_title,
            event_name=safe_event_name,
            event_desc=safe_event_desc,
            chapter_id=event.chapter_id or "未知",
            time_desc=safe_time_desc,
            location=safe_location,
            participants=participants_text,
            context=safe_context
        )
        
        # 检查是否需要使用模拟数据
        logger.info("USE_MOCK_DATA设置为: %s", settings.USE_MOCK_DATA)
        
        # 如果设置了强制使用真实API,不管USE_MOCK_DATA如何设置
        force_real_api = True
        logger.info("强制使用真实API: %s", force_real_api)
        
        if settings.USE_MOCK_DATA and not force_real_api:
            logger.warning("根据配置使用模拟数据而非调用真实API")
            return generate_sample_significance(event)
        
        # 调用OpenAI API
        logger.info("准备调用OpenAI API...")
        logger.info("API密钥: %s...（已隐藏部分）", settings.OPENAI_API_KEY[:5] if settings.OPENAI_API_KEY else "未设置")
        logger.info("API基础URL: %s", settings.OPENAI_API_BASE)
        logger.info("使用的模型: %s", settings.OPENAI_API_MODEL)
        
        openai_client = OpenAIClient()
        response = await openai_client.chat_completion(
            messages=[
                {"role": "system", "content": "你是一个小说分析助手，擅长分析小说中事件的重要性和影响。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        
        # 记录API响应
        logger.info("OpenAI API响应: %s...", str(response)[:200] if response else "无响应")
        
        # 解析响应
        if not response or "choices" not in response:
            logger.error("OpenAI API返回无效响应")
            return generate_sample_significance(event)
            
        content = response["choices"][0]["message"]["content"]
        logger.info("API响应内容: %s...", content[:200] if content else "无内容")
        
        try:
            # 提取JSON部分
            import re
            import json
            
            # 尝试找到并提取JSON部分
            json_match = re.search(r'```json\s*([\s\S]*?)\s*```', content)
            if json_match:
                json_str = json_match.group(1)
                logger.info("成功找到JSON代码块")
            else:
                # 如果没有找到```json标记，尝试直接解析整个内容
                json_str = content
                logger.info("未找到JSON代码块，尝试直接解析整个内容")
            
            # 清理并解析JSON
            json_str = OpenAIClient.clean_json_content(json_str)
            logger.info("清理后的JSON字符串: %s...", json_str[:200] if json_str else "无内容")
            
            result = json.loads(json_str)
            logger.info("JSON解析成功")
            
            logger.info("成功分析事件ID %d '%s' 的重要性", event_id, safe_event_name)
            return result
        except Exception as json_error:
            logger.error("JSON解析失败: %s", str(json_error))
            logger.error("原始JSON字符串: %s", json_str if 'json_str' in locals() else "未定义")
            return generate_sample_significance(event)
        
    except Exception as e:
        logger.error("分析事件重要性失败: %s", str(e))
        logger.error("错误类型: %s", type(e).__name__)
        import traceback
        logger.error("详细错误信息: %s", traceback.format_exc())
        logger.error("使用备用方法生成事件重要性分析")
        # 如果AI分析失败，返回模拟数据
        return generate_sample_significance(event)

def generate_sample_significance(event) -> Dict[str, Any]:
    """
    生成示例事件重要性分析（当AI分析失败时使用）
    
    Args:
        event: 事件对象
        
    Returns:
        Dict[str, Any]: 事件重要性分析
    """
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