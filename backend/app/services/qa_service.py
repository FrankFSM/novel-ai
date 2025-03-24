import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.openai_client import OpenAIClient
from app.models import schemas

logger = logging.getLogger(__name__)

async def answer_question(
    db: Session, 
    novel_id: int,
    question: str,
    use_rag: bool = True
) -> schemas.AnswerResponse:
    """
    回答关于小说的问题
    
    Args:
        db: 数据库会话
        novel_id: 小说ID
        question: 用户问题
        use_rag: 是否使用检索增强生成
        
    Returns:
        回答结果
    """
    try:
        sources = []
        
        if use_rag:
            # 1. 检索相关文本
            relevant_chunks = await retrieve_relevant_chunks(db, novel_id, question)
            
            # 2. 准备上下文
            context = ""
            for chunk in relevant_chunks:
                context += f"内容片段 (章节 {chunk['chapter_title']}):\n{chunk['content']}\n\n"
                sources.append({
                    "chapter_id": chunk["chapter_id"],
                    "chapter_title": chunk["chapter_title"],
                    "content": chunk["content"][:100] + "..." if len(chunk["content"]) > 100 else chunk["content"]
                })
                
            # 3. 构建提示
            system_prompt = """
            你是一个专门回答关于小说内容的AI助手。请根据提供的小说内容片段回答用户问题。
            如果无法从内容片段中找到答案，请明确说明。不要编造不在内容中的信息。
            回答要详细、准确，并引用相关文本来支持你的回答。
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"根据以下小说内容片段回答问题:\n\n{context}\n\n问题: {question}"}
            ]
        else:
            # 不使用RAG，直接问LLM
            # 获取小说基本信息
            from app.services.novel_service import get_novel
            novel = get_novel(db, novel_id)
            
            system_prompt = f"""
            你是一个专门回答关于小说《{novel.title}》(作者: {novel.author})的AI助手。
            请尽量根据你对这部小说的了解回答用户问题。如果不确定，请明确说明。
            """
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question}
            ]
        
        # 4. 调用OpenAI API
        response = await OpenAIClient.chat_completion(messages=messages, temperature=0.3)
        
        # 5. 解析回答
        answer = response["choices"][0]["message"]["content"]
        
        # 6. 计算置信度
        confidence = 0.9 if use_rag and sources else 0.6
        
        return {
            "answer": answer,
            "sources": sources,
            "confidence": confidence
        }
        
    except Exception as e:
        logger.error(f"回答问题失败: {str(e)}")
        raise

async def retrieve_relevant_chunks(
    db: Session, 
    novel_id: int, 
    query: str,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    检索与问题相关的文本块
    
    Args:
        db: 数据库会话
        novel_id: 小说ID
        query: 查询问题
        limit: 返回结果数量限制
        
    Returns:
        相关文本块列表
    """
    try:
        # 1. 获取问题的向量表示
        query_embedding = await OpenAIClient.get_embedding(query)
        
        # 2. 从向量数据库检索相似文本
        from pymilvus import Collection
        collection = Collection("novel_chunks")
        collection.load()
        
        search_params = {
            "metric_type": "COSINE",
            "params": {"ef": 64}
        }
        
        results = collection.search(
            data=[query_embedding],
            anns_field="embedding",
            param=search_params,
            limit=limit,
            expr=f"novel_id == {novel_id}"
        )
        
        # 3. 获取检索结果
        chunk_ids = [hit.id for hit in results[0]]
        
        # 4. 从数据库获取文本内容
        from sqlalchemy import text
        
        result = []
        for chunk_id in chunk_ids:
            sql = text("""
                SELECT 
                    tc.id, tc.content, tc.start_char, tc.end_char, 
                    c.id as chapter_id, c.title as chapter_title, c.number as chapter_number
                FROM 
                    text_chunks tc
                JOIN 
                    chapters c ON tc.chapter_id = c.id
                WHERE 
                    tc.vector_id = :vector_id
            """)
            
            chunk_data = db.execute(sql, {"vector_id": str(chunk_id)}).fetchone()
            
            if chunk_data:
                result.append({
                    "id": chunk_data.id,
                    "content": chunk_data.content,
                    "start_char": chunk_data.start_char,
                    "end_char": chunk_data.end_char,
                    "chapter_id": chunk_data.chapter_id,
                    "chapter_title": chunk_data.chapter_title,
                    "chapter_number": chunk_data.chapter_number
                })
        
        return result
        
    except Exception as e:
        logger.error(f"检索相关文本失败: {str(e)}")
        raise

async def extract_entities(text: str) -> schemas.EntityExtractionResponse:
    """
    从文本中提取实体
    
    Args:
        text: 文本内容
        
    Returns:
        提取的实体
    """
    try:
        # 调用OpenAI客户端提取实体
        entities = await OpenAIClient.extract_entities(text)
        return entities
    except Exception as e:
        logger.error(f"实体提取失败: {str(e)}")
        raise

async def analyze_text(text: str) -> Dict[str, Any]:
    """
    分析文本
    
    Args:
        text: 文本内容
        
    Returns:
        分析结果
    """
    try:
        system_prompt = """
        你是一个专门分析小说文本的AI助手。请从以下文本中分析：
        1. 文本主题和情感基调
        2. 文本中的主要冲突
        3. 文本中表现出的角色性格特征
        4. 可能的伏笔和隐喻
        
        以JSON格式返回分析结果，格式为:
        {
          "theme": {"main": "主题", "description": "详细描述"},
          "emotions": ["情感1", "情感2", ...],
          "conflicts": [{"type": "冲突类型", "description": "冲突描述"}],
          "character_traits": [{"character": "角色名", "traits": ["特征1", "特征2", ...]}],
          "foreshadowing": [{"description": "伏笔描述", "confidence": 0-1之间的置信度}]
        }
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请分析以下小说片段:\n\n{text}"}
        ]
        
        functions = [{
            "name": "analyze_novel_text",
            "description": "分析小说文本片段的主题、情感和伏笔等",
            "parameters": {
                "type": "object",
                "properties": {
                    "theme": {
                        "type": "object",
                        "properties": {
                            "main": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    },
                    "emotions": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "conflicts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type": {"type": "string"},
                                "description": {"type": "string"}
                            }
                        }
                    },
                    "character_traits": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "character": {"type": "string"},
                                "traits": {"type": "array", "items": {"type": "string"}}
                            }
                        }
                    },
                    "foreshadowing": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "description": {"type": "string"},
                                "confidence": {"type": "number"}
                            }
                        }
                    }
                }
            }
        }]
        
        response = await OpenAIClient.chat_completion(
            messages=messages,
            temperature=0.3,
            functions=functions,
            function_call={"name": "analyze_novel_text"}
        )
        
        function_call = response["choices"][0]["message"].get("function_call")
        if function_call and function_call.get("name") == "analyze_novel_text":
            import json
            return json.loads(function_call.get("arguments", "{}"))
        
        return {}
        
    except Exception as e:
        logger.error(f"文本分析失败: {str(e)}")
        raise 