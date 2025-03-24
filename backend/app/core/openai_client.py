import openai
import logging
from typing import List, Dict, Any, Optional
from app.core.config import settings

# 配置OpenAI API
openai.api_key = settings.OPENAI_API_KEY
if settings.OPENAI_API_BASE:
    openai.api_base = settings.OPENAI_API_BASE

logger = logging.getLogger(__name__)

class OpenAIClient:
    """OpenAI API客户端封装"""
    
    @staticmethod
    async def get_embedding(text: str) -> List[float]:
        """获取文本嵌入向量"""
        try:
            response = await openai.Embedding.acreate(
                input=text,
                model="text-embedding-ada-002"
            )
            return response["data"][0]["embedding"]
        except Exception as e:
            logger.error(f"获取嵌入向量失败: {str(e)}")
            raise
    
    @staticmethod
    async def chat_completion(
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2000,
        functions: Optional[List[Dict[str, Any]]] = None,
        function_call: Optional[str] = None
    ) -> Dict[str, Any]:
        """调用聊天完成API"""
        try:
            kwargs = {
                "model": settings.OPENAI_API_MODEL,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
            
            if functions:
                kwargs["functions"] = functions
                
            if function_call:
                kwargs["function_call"] = function_call
                
            response = await openai.ChatCompletion.acreate(**kwargs)
            return response
        except Exception as e:
            logger.error(f"聊天完成API调用失败: {str(e)}")
            raise
    
    @staticmethod
    async def extract_entities(text: str) -> Dict[str, Any]:
        """从文本中提取实体"""
        system_prompt = """
        你是一个专门从小说文本中提取结构化信息的AI助手。请从以下文本中提取：
        1. 人物(PERSON)：所有人物名称
        2. 地点(LOCATION)：所有地点名称
        3. 物品(ITEM)：重要物品、法宝、武器等
        4. 事件(EVENT)：重要事件
        5. 时间(TIME)：时间点或时间段
        
        以JSON格式返回，格式为:
        {
          "persons": [{"name": "名称", "alias": ["别名1", "别名2"], "description": "简短描述"}],
          "locations": [{"name": "名称", "description": "简短描述"}],
          "items": [{"name": "名称", "owner": "拥有者", "description": "简短描述"}],
          "events": [{"name": "事件名", "participants": ["参与者1", "参与者2"], "description": "事件描述"}],
          "times": [{"time": "时间表述", "description": "简短描述"}]
        }
        """
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"请从以下小说片段中提取结构化信息：\n\n{text}"}
        ]
        
        functions = [{
            "name": "extract_novel_entities",
            "description": "从小说文本中提取结构化实体信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "persons": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "alias": {"type": "array", "items": {"type": "string"}},
                                "description": {"type": "string"}
                            }
                        }
                    },
                    "locations": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "description": {"type": "string"}
                            }
                        }
                    },
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "owner": {"type": "string"},
                                "description": {"type": "string"}
                            }
                        }
                    },
                    "events": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "participants": {"type": "array", "items": {"type": "string"}},
                                "description": {"type": "string"}
                            }
                        }
                    },
                    "times": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "time": {"type": "string"},
                                "description": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }]
        
        response = await OpenAIClient.chat_completion(
            messages=messages,
            temperature=0.1,
            functions=functions,
            function_call={"name": "extract_novel_entities"}
        )
        
        function_call = response.choices[0].message.get("function_call")
        if function_call and function_call.get("name") == "extract_novel_entities":
            import json
            return json.loads(function_call.get("arguments", "{}"))
        
        return {} 