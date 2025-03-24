import logging
import time
import os
import json
from typing import List, Dict, Any, Optional
import re

# 尝试使用新版本的导入方式
try:
    from openai import OpenAI
    is_new_api = True
    logger = logging.getLogger(__name__)
    logger.info("使用新版本OpenAI API (>=1.0.0)")
except ImportError:
    # 如果失败，使用旧版本的导入方式
    import openai
    is_new_api = False
    logger = logging.getLogger(__name__)
    logger.info("使用旧版本OpenAI API (<1.0.0)")

from app.core.config import settings

# 配置OpenAI客户端
client = None
try:
    if settings.OPENAI_API_KEY:
        if is_new_api:
            client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_API_BASE
            )
        else:
            # 旧版本API初始化方式
            openai.api_key = settings.OPENAI_API_KEY
            openai.api_base = settings.OPENAI_API_BASE
            
        logger.info(f"OpenAI客户端初始化成功，使用API基础URL: {settings.OPENAI_API_BASE}")
    else:
        logger.warning("未设置OpenAI API密钥，将使用模拟数据")
        print("未设置OpenAI API密钥，将使用模拟数据")
except Exception as e:
    logger.error(f"OpenAI客户端初始化失败: {str(e)}")
    # 不直接退出，可以通过USE_MOCK_DATA提供模拟数据

class OpenAIClient:
    """OpenAI API客户端封装"""
    
    @staticmethod
    async def get_embedding(text: str) -> List[float]:
        """获取文本嵌入向量"""
        if settings.USE_MOCK_DATA:
            # 返回模拟的嵌入向量
            import numpy as np
            return list(np.random.randn(settings.VECTOR_DIMENSION))
            
        try:
            if not client and not is_new_api:
                raise ValueError("OpenAI客户端未初始化")
                
            if is_new_api:
                if not client:
                    raise ValueError("OpenAI客户端未初始化")
                response = client.embeddings.create(
                    input=text,
                    model="text-embedding-ada-002"
                )
                return response.data[0].embedding
            else:
                # 旧版本API调用方式
                response = openai.Embedding.create(
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
        function_call: Optional[str] = None,
        max_retries: int = 3,
        retry_delay: float = 2.0,
        timeout: float = 60.0
    ) -> Dict[str, Any]:
        """
        调用OpenAI Chat API
        """
        try:
            logger.info(f"使用模型 {settings.OPENAI_API_MODEL} 调用OpenAI API")
            
            client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_API_BASE
            )
            
            response = client.chat.completions.create(
                model=settings.OPENAI_API_MODEL,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                functions=functions,
                function_call=function_call
            )
            
            # 将响应对象转换为字典格式
            return {
                "choices": [{
                    "message": {
                        "content": response.choices[0].message.content,
                        "role": response.choices[0].message.role,
                        "function_call": response.choices[0].message.function_call if hasattr(response.choices[0].message, 'function_call') else None
                    }
                }]
            }
            
        except Exception as e:
            logger.error(f"OpenAI API调用失败: {str(e)}")
            raise
    
    @staticmethod
    async def extract_character_relationships(text: str) -> Dict[str, Any]:
        """从文本中提取人物关系图。

        Args:
            text: 输入文本

        Returns:
            包含节点和边的字典
        """
        try:
            # 如果配置为使用模拟数据，直接返回
            if settings.USE_MOCK_DATA:
                logger.info("已配置使用模拟数据，跳过API调用")
                return OpenAIClient.generate_mock_relationship_data()

            system_prompt = """你是一个专业的小说分析助手。请分析输入的文本，提取出所有人物及其关系，并按以下JSON格式输出：
{
    "nodes": [
        {
            "id": 1,
            "name": "人物名称",
            "description": "人物描述",
            "importance": 1-5的重要性评分
        }
    ],
    "edges": [
        {
            "source_id": 1,
            "target_id": 2,
            "source_name": "源节点人物名称",
            "target_name": "目标节点人物名称",
            "relation": "关系类型",
            "description": "关系描述",
            "importance": 1-5的重要性评分
        }
    ]
}

注意：
1. 每个人物都应该有唯一的id
2. 关系是有向的，source指向target
3. 重要性评分1-5，5分最重要
4. 请确保输出是合法的JSON格式
5. 不要输出任何额外的解释或分析，只返回JSON数据
"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]

            # 初始化客户端
            client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_API_BASE
            )
            
            # 直接调用API
            response = client.chat.completions.create(
                model=settings.OPENAI_API_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            # 获取响应内容
            content = response.choices[0].message.content
            logger.info("\n===原始响应===\n%s", content)
            
            # 尝试解析JSON
            try:
                # 清理内容，移除可能的前缀说明
                cleaned_content = content
                prefixes = [
                    "好的，", "这是", "以下是", "根据文本，", 
                    "分析结果：", "人物关系图：", "JSON格式如下：",
                    "```json", "```"
                ]
                for prefix in prefixes:
                    if cleaned_content.startswith(prefix):
                        cleaned_content = cleaned_content[len(prefix):].strip()
                
                # 尝试直接解析
                try:
                    data = json.loads(cleaned_content)
                    if "nodes" in data and "edges" in data:
                        logger.info("方法1成功：直接解析")
                        return data
                except json.JSONDecodeError:
                    pass
                
                # 尝试提取大括号内容
                try:
                    pattern = r'\{[\s\S]*\}'  # 匹配包括换行符在内的所有字符
                    match = re.search(pattern, cleaned_content)
                    if match:
                        data = json.loads(match.group())
                        if "nodes" in data and "edges" in data:
                            logger.info("方法2成功：提取大括号内容")
                            return data
                except (json.JSONDecodeError, AttributeError):
                    pass
                
                # 尝试从代码块中提取
                try:
                    pattern = r'```(?:json)?\s*([\s\S]*?)\s*```'  # 匹配包括换行符的代码块
                    match = re.search(pattern, content)
                    if match:
                        data = json.loads(match.group(1))
                        if "nodes" in data and "edges" in data:
                            logger.info("方法3成功：从代码块提取")
                            return data
                except (json.JSONDecodeError, AttributeError):
                    pass
                
                raise ValueError("无法从响应中提取有效的JSON数据")
                
            except Exception as e:
                logger.error("JSON解析失败: %s", str(e))
                logger.error("原始内容: %s", content)
                raise
            
        except Exception as e:
            logger.error("提取人物关系时出错: %s", str(e))
            # 返回模拟数据
            return OpenAIClient.generate_mock_relationship_data()
    
    @staticmethod
    def generate_mock_relationship_data() -> Dict[str, Any]:
        """生成模拟的人物关系数据（当API不可用时使用）"""
        return {
            "nodes": [
                {"id": 1, "name": "林惜", "description": "女主角，天才炼丹师", "importance": 5},
                {"id": 2, "name": "秦煜", "description": "男主角，剑修", "importance": 5},
                {"id": 3, "name": "王长老", "description": "仙门长老", "importance": 3},
                {"id": 4, "name": "李师兄", "description": "秦煜的师兄", "importance": 2},
                {"id": 5, "name": "赵敏", "description": "林惜的闺蜜", "importance": 3},
                {"id": 6, "name": "古尘", "description": "隐世高人", "importance": 4},
                {"id": 7, "name": "黑袍人", "description": "神秘反派", "importance": 4}
            ],
            "edges": [
                {"source_id": 1, "target_id": 2, "source_name": "林惜", "target_name": "秦煜", "relation": "恋人", "description": "青梅竹马，共同修行", "importance": 5},
                {"source_id": 2, "target_id": 3, "source_name": "秦煜", "target_name": "王长老", "relation": "师徒", "description": "王长老是秦煜的恩师", "importance": 4},
                {"source_id": 1, "target_id": 5, "source_name": "林惜", "target_name": "赵敏", "relation": "朋友", "description": "情同姐妹的闺蜜", "importance": 3},
                {"source_id": 2, "target_id": 4, "source_name": "秦煜", "target_name": "李师兄", "relation": "同门", "description": "同门师兄弟，亦师亦友", "importance": 2},
                {"source_id": 6, "target_id": 1, "source_name": "古尘", "target_name": "林惜", "relation": "师徒", "description": "隐世高人收林惜为徒", "importance": 4},
                {"source_id": 7, "target_id": 2, "source_name": "黑袍人", "target_name": "秦煜", "relation": "敌人", "description": "有不共戴天之仇", "importance": 4},
                {"source_id": 3, "target_id": 6, "source_name": "王长老", "target_name": "古尘", "relation": "旧识", "description": "多年前的故交", "importance": 2},
                {"source_id": 7, "target_id": 6, "source_name": "黑袍人", "target_name": "古尘", "relation": "仇敌", "description": "曾经的同门，如今势不两立", "importance": 5}
            ]
        }
    
    @staticmethod
    async def extract_entities(text: str) -> Dict[str, Any]:
        """从文本中提取实体。

        Args:
            text: 输入文本

        Returns:
            包含不同类型实体的字典
        """
        try:
            # 如果配置为使用模拟数据，直接返回
            if settings.USE_MOCK_DATA:
                logger.info("已配置使用模拟数据，跳过API调用")
                return OpenAIClient.generate_mock_entities_data()

            system_prompt = """你是一个专业的小说分析助手。请分析输入的文本，提取出所有实体，并按以下JSON格式输出：
{
    "persons": [
        {
            "name": "人物名称",
            "alias": ["别名1", "别名2"],
            "description": "人物描述",
            "importance": 1-5的重要性评分
        }
    ],
    "locations": [
        {
            "name": "地点名称",
            "description": "地点描述",
            "importance": 1-5的重要性评分
        }
    ],
    "items": [
        {
            "name": "物品名称",
            "description": "物品描述",
            "importance": 1-5的重要性评分
        }
    ],
    "events": [
        {
            "name": "事件名称",
            "description": "事件描述",
            "importance": 1-5的重要性评分
        }
    ],
    "times": [
        {
            "name": "时间点/时间段",
            "description": "时间描述"
        }
    ]
}

注意：
1. 每个实体都应该有完整的属性
2. 重要性评分1-5，5分最重要
3. 请确保输出是合法的JSON格式
4. 不要输出任何额外的解释或分析，只返回JSON数据
"""
            
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"请从以下文本中提取实体：\n\n{text}"}
            ]

            # 初始化客户端
            client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_API_BASE
            )
            
            # 直接调用API
            response = client.chat.completions.create(
                model=settings.OPENAI_API_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=2000
            )
            
            # 获取响应内容
            content = response.choices[0].message.content
            logger.info("\n===原始响应===\n%s", content)
            
            # 尝试解析JSON
            def extract_json(text):
                # 清理内容，移除可能的前缀说明
                cleaned_content = text
                prefixes = [
                    "好的，", "这是", "以下是", "根据文本，", 
                    "分析结果：", "实体提取结果：", "JSON格式如下：",
                    "```json", "```"
                ]
                for prefix in prefixes:
                    if cleaned_content.startswith(prefix):
                        cleaned_content = cleaned_content[len(prefix):].strip()
                
                # 方法1：直接尝试解析整个内容
                try:
                    data = json.loads(cleaned_content)
                    if all(key in data for key in ["persons", "locations", "items", "events", "times"]):
                        logger.info("方法1成功：直接解析整个内容")
                        return data
                except json.JSONDecodeError:
                    pass
                
                # 方法2：查找第一个{和最后一个}之间的内容
                try:
                    start = cleaned_content.find('{')
                    end = cleaned_content.rfind('}') + 1
                    if start >= 0 and end > start:
                        json_str = cleaned_content[start:end]
                        data = json.loads(json_str)
                        if all(key in data for key in ["persons", "locations", "items", "events", "times"]):
                            logger.info("方法2成功：提取大括号内容")
                            return data
                except json.JSONDecodeError:
                    pass
                
                # 方法3：查找代码块
                try:
                    matches = re.finditer(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
                    for match in matches:
                        try:
                            data = json.loads(match.group(1))
                            if all(key in data for key in ["persons", "locations", "items", "events", "times"]):
                                logger.info("方法3成功：从代码块提取")
                                return data
                        except json.JSONDecodeError:
                            continue
                except Exception:
                    pass
                
                return None
            
            # 尝试解析JSON
            parsed_data = extract_json(content)
            
            if parsed_data:
                logger.info("成功解析实体数据")
                return parsed_data
            else:
                logger.error("无法从响应中提取有效的JSON数据")
                return OpenAIClient.generate_mock_entities_data()
            
        except Exception as e:
            logger.error(f"提取实体时出错: {str(e)}")
            # 返回模拟数据
            return OpenAIClient.generate_mock_entities_data()
            
    @staticmethod
    def generate_mock_entities_data() -> Dict[str, Any]:
        """生成模拟的实体数据（当API不可用时使用）"""
        return {
            "persons": [
                {"name": "林惜", "alias": ["小惜", "惜儿"], "description": "女主角，天才炼丹师"},
                {"name": "秦煜", "alias": ["煜哥"], "description": "男主角，剑修"},
                {"name": "王长老", "alias": [], "description": "仙门长老"},
                {"name": "李师兄", "alias": ["李寒"], "description": "秦煜的师兄"}
            ],
            "locations": [
                {"name": "青云门", "description": "主角所在门派"},
                {"name": "万剑峰", "description": "秦煜修炼之地"},
                {"name": "丹心阁", "description": "林惜炼丹之处"}
            ],
            "items": [
                {"name": "青霜剑", "owner": "秦煜", "description": "秦煜的佩剑，上品法器"},
                {"name": "丹炉", "owner": "林惜", "description": "林惜炼丹用的宝贝"}
            ],
            "events": [
                {"name": "比武大会", "participants": ["秦煜", "李师兄"], "description": "门派举行的年度比武"},
                {"name": "炼丹大赛", "participants": ["林惜"], "description": "各门派炼丹师的较量"}
            ],
            "times": [
                {"time": "三年前", "description": "主角进入门派的时间"},
                {"time": "半月后", "description": "比武大会开始的时间"}
            ]
        }
    
    @staticmethod
    def check_api_connectivity() -> Dict[str, Any]:
        """检查与OpenAI API的连接状态"""
        results = {
            "can_connect": False,
            "api_key_valid": False,
            "details": [],
            "suggestions": []
        }
        
        # 检查API密钥是否设置
        if not settings.OPENAI_API_KEY:
            results["details"].append("API密钥未设置")
            results["suggestions"].append("在环境变量或.env文件中设置OPENAI_API_KEY")
            return results
            
        # 检查API密钥格式
        if not settings.OPENAI_API_KEY.startswith("sk-"):
            results["details"].append("API密钥格式不正确（应以'sk-'开头）")
            results["suggestions"].append("确保使用正确格式的OpenAI API密钥")
        
        # 提取API基础URL中的主机和端口
        import urllib.parse
        api_base = settings.OPENAI_API_BASE or "https://api.openai.com/v1"
        parsed_url = urllib.parse.urlparse(api_base)
        host = parsed_url.netloc.split(':')[0]
        port = parsed_url.port or (443 if parsed_url.scheme == "https" else 80)
        
        # 测试网络连接
        import socket
        try:
            # 尝试连接到API服务器
            socket.create_connection((host, port), timeout=10)
            results["can_connect"] = True
            results["details"].append(f"可以连接到{host}:{port}")
        except Exception as e:
            results["details"].append(f"无法连接到API服务器: {str(e)}")
            results["suggestions"].append("检查您的网络连接和防火墙设置")
        
        # 如果能连接，测试API密钥
        if results["can_connect"]:
            try:
                if is_new_api and client:
                    # 新版本API测试
                    response = client.models.list()
                    results["api_key_valid"] = True
                    results["details"].append("API密钥有效")
                elif not is_new_api:
                    # 旧版本API测试
                    response = openai.Model.list()
                    results["api_key_valid"] = True
                    results["details"].append("API密钥有效")
                else:
                    results["details"].append("API客户端未初始化")
            except Exception as e:
                error_str = str(e)
                results["details"].append(f"API密钥验证失败: {error_str}")
                
                # 添加更具体的建议
                if "authentication" in error_str.lower():
                    results["suggestions"].append("检查API密钥是否正确")
                elif "not found" in error_str.lower() or "not supported" in error_str.lower():
                    results["suggestions"].append(f"检查模型'{settings.OPENAI_API_MODEL}'是否在当前API提供商支持")
                else:
                    results["suggestions"].append("检查API密钥是否正确，以及账户余额是否充足")
        
        return results 