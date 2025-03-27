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

            system_prompt = """你是一个专业的文学分析师，专注于提取小说中的人物关系网络。分析文本中所有角色及其关系，并以JSON格式输出：
{
    "nodes": [
        {
            "id": 1,
            "name": "人物名称",
            "description": "人物详细描述",
            "importance": 1-5的重要性评分
        }
    ],
    "edges": [
        {
            "source_id": 1,
            "target_id": 2,
            "source_name": "源角色名称",
            "target_name": "目标角色名称",
            "relation": "关系类型",
            "description": "关系详细描述及证据",
            "importance": 0.1-1.0的关系重要性评分
        }
    ]
}

关键要求：
1. 分析所有角色，包括背景角色（如"姓阮的外乡铁匠"）
2. 标准化角色名称：
   - 统一命名格式，例如"卖鱼的中年人"和"卖鱼中年人"应识别为同一角色
   - 将相似描述的同一角色合并为一个实体
   - 对无明确姓名的角色，使用职业+特征+性别/年龄格式
3. 关注以下关系类型：
   - 师徒关系（如刘羡阳和姚老头）
   - 交易关系（如锦衣少年与陈平安）
   - 社交关系、敌对关系、主仆关系、家族关系
4. 为不确定姓名的角色使用描述作为名称
5. 每个角色使用唯一ID
6. 提供关系的文本证据
7. 角色重要性1-5分，关系重要性0.1-1.0
8. 返回纯JSON，不含额外解释
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
                max_tokens=3000
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
                        logger.info(f"方法1成功：直接解析，找到{len(data['nodes'])}个角色，{len(data['edges'])}个关系")
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
                            logger.info(f"方法2成功：提取大括号内容，找到{len(data['nodes'])}个角色，{len(data['edges'])}个关系")
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
                            logger.info(f"方法3成功：从代码块提取，找到{len(data['nodes'])}个角色，{len(data['edges'])}个关系")
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
                {"id": 7, "name": "黑袍人", "description": "神秘反派", "importance": 4},
                {"id": 8, "name": "张衡", "description": "李师兄的师弟，秦煜的同门", "importance": 2}
            ],
            "edges": [
                {"source_id": 2, "target_id": 1, "source_name": "秦煜", "target_name": "林惜", "relation": "恋人", "description": "青梅竹马，共同修行", "importance": 5},
                {"source_id": 3, "target_id": 2, "source_name": "王长老", "target_name": "秦煜", "relation": "师徒", "description": "王长老是秦煜的恩师", "importance": 4},
                {"source_id": 3, "target_id": 4, "source_name": "王长老", "target_name": "李师兄", "relation": "师徒", "description": "王长老是李师兄的师傅", "importance": 3},
                {"source_id": 3, "target_id": 8, "source_name": "王长老", "target_name": "张衡", "relation": "师徒", "description": "王长老是张衡的师傅", "importance": 3},
                {"source_id": 1, "target_id": 5, "source_name": "林惜", "target_name": "赵敏", "relation": "朋友", "description": "情同姐妹的闺蜜", "importance": 3},
                {"source_id": 2, "target_id": 4, "source_name": "秦煜", "target_name": "李师兄", "relation": "同门", "description": "同门师兄弟，亦师亦友", "importance": 2},
                {"source_id": 2, "target_id": 8, "source_name": "秦煜", "target_name": "张衡", "relation": "同门", "description": "同门师兄弟", "importance": 2},
                {"source_id": 4, "target_id": 8, "source_name": "李师兄", "target_name": "张衡", "relation": "同门", "description": "同门师兄弟", "importance": 2},
                {"source_id": 6, "target_id": 1, "source_name": "古尘", "target_name": "林惜", "relation": "师徒", "description": "隐世高人收林惜为徒", "importance": 4},
                {"source_id": 7, "target_id": 2, "source_name": "黑袍人", "target_name": "秦煜", "relation": "敌人", "description": "有不共戴天之仇", "importance": 4},
                {"source_id": 7, "target_id": 1, "source_name": "黑袍人", "target_name": "林惜", "relation": "敌人", "description": "因秦煜而成为敌人", "importance": 3},
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
            "parent": "所属更大地点（如有）",
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

关于地点识别的重要说明：
1. 地点必须是确实存在的物理空间或区域，如城市、房间、建筑、山脉、宫殿等
2. 以下类型不应被识别为地点：
   - 物品或藏品（如"库藏瓷器"、"家传宝剑"）
   - 人群或组织（如"朝廷大臣"、"江湖帮派"）
   - 抽象概念（如"修炼境界"、"剑道"）
   - 收藏品或展览（如"字画收藏"、"瓷器展"）
3. 地点通常具有以下特征：
   - 人物可以在其中移动、停留或居住
   - 有明确的物理边界或范围
   - 在故事中作为事件发生的场所

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
                {"name": "青云门", "description": "主角所在门派", "parent": null, "importance": 5},
                {"name": "万剑峰", "description": "秦煜修炼之地", "parent": "青云门", "importance": 4},
                {"name": "丹心阁", "description": "林惜炼丹之处", "parent": "青云门", "importance": 4}
            ],
            "items": [
                {"name": "青霜剑", "owner": "秦煜", "description": "秦煜的佩剑，上品法器", "importance": 4},
                {"name": "丹炉", "owner": "林惜", "description": "林惜炼丹用的宝贝", "importance": 3}
            ],
            "events": [
                {"name": "比武大会", "participants": ["秦煜", "李师兄"], "description": "门派举行的年度比武", "importance": 4},
                {"name": "炼丹大赛", "participants": ["林惜"], "description": "各门派炼丹师的较量", "importance": 4}
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

    @staticmethod
    async def analyze_characters(content: str, is_chapter_specific: bool = False) -> List[Dict[str, Any]]:
        """分析文本中的人物角色
        
        Args:
            content: 文本内容
            is_chapter_specific: 是否为单章节特定分析
            
        Returns:
            角色信息列表
        """
        try:
            # 构建系统提示
            system_prompt = """你是一个优秀的文学分析专家，擅长分析小说中的人物角色。
请仔细分析以下文本，提取出所有出现的角色，并提供以下信息：
1. 角色名称
2. 角色别名（如有）
3. 角色描述（性格、外貌、背景等）
4. 角色重要性（1-5，5为最重要）

"""
            if is_chapter_specific:
                system_prompt += """注意，这是小说的单个章节，请只分析该章节中出现的角色及其在本章中的表现。
不要猜测或推断角色在其他章节中的信息。"""
            
            # 构建用户提示
            user_prompt = f"""请分析以下文本中的角色，并以JSON格式返回结果。每个角色包括name(角色名)、alias(别名数组)、description(描述)、importance(重要性1-5)等字段。
            
文本内容:
{content}

请以JSON数组格式返回，例如：
[
  {{
    "name": "角色A",
    "alias": ["别名1", "别名2"],
    "description": "角色A的描述...",
    "importance": 5
  }},
  {{
    "name": "角色B",
    "alias": [],
    "description": "角色B的描述...",
    "importance": 3
  }}
]"""

            # 如果配置为使用模拟数据，返回模拟数据
            if settings.USE_MOCK_DATA:
                logger.info("使用模拟数据进行角色分析")
                return OpenAIClient.generate_mock_characters_data()

            # 初始化客户端
            logger.info(f"初始化OpenAI客户端，使用API基础URL: {settings.OPENAI_API_BASE}")
            client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_API_BASE
            )
            
            # 调用OpenAI API
            logger.info(f"调用OpenAI API进行角色分析，使用模型: {settings.OPENAI_API_MODEL}")
            response = client.chat.completions.create(
                model=settings.OPENAI_API_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            
            result_text = response.choices[0].message.content
            logger.info(f"OpenAI API返回结果: {result_text[:200]}...")
            
            # 尝试清理和解析JSON响应
            try:
                # 清理可能的前缀和后缀
                json_pattern = r'(\{|\[).*(\}|\])'
                json_matches = re.search(json_pattern, result_text, re.DOTALL)
                if json_matches:
                    cleaned_text = json_matches.group(0)
                    logger.info(f"提取到JSON内容: {cleaned_text[:100]}...")
                else:
                    cleaned_text = result_text
                
                # 尝试解析JSON
                result_json = json.loads(cleaned_text)
            except json.JSONDecodeError as je:
                logger.error(f"无法解析JSON响应: {str(je)}")
                logger.error(f"原始响应: {result_text}")
                raise ValueError(f"API返回了无效的JSON格式: {str(je)}")
            
            # 确保返回的是数组，如果是包含characters字段的对象，则取出characters
            if isinstance(result_json, dict):
                if "characters" in result_json:
                    result = result_json["characters"]
                else:
                    result = result_json.get("characters", result_json)
            else:
                # 如果已经是列表，直接使用
                result = result_json
            
            # 确保结果是列表类型
            if not isinstance(result, list):
                error_msg = f"分析结果不是列表格式: {type(result)}"
                logger.error(error_msg)
                raise ValueError(error_msg)
            
            logger.info(f"成功解析角色分析结果，共{len(result)}个角色")
            return result
        
        except Exception as e:
            logger.error(f"角色分析失败: {str(e)}")
            logger.exception("角色分析过程中发生异常")
            # 不再返回模拟数据，而是抛出异常
            raise
    
    @staticmethod
    async def analyze_character_personality(text: str, character_name: str) -> Dict[str, Any]:
        """分析指定角色的性格和特点
        
        Args:
            text: 小说文本内容
            character_name: 角色名称
            
        Returns:
            角色性格分析结果
        """
        try:
            logger.info(f"开始分析角色 '{character_name}' 的性格...")

            system_prompt = f"""你是一个专业的文学角色分析师。请深入分析输入文本中的角色"{character_name}"，
提取其性格特点、行为模式、心理动机和价值观等，并按以下JSON格式输出结果：

{{
    "name": "{character_name}",
    "personality": ["性格特点1", "性格特点2", ...],
    "traits": [
        {{
            "trait": "特质名称",
            "description": "详细解释",
            "evidence": "文本中的证据"
        }}
    ],
    "description": "全面的角色描述",
    "analysis": "详细的性格分析，包括人物在故事中的发展变化",
    "quotes": ["角色经典台词1", "角色经典台词2", ...]
}}

特别注意：
1. 仔细分析角色的所有方面，包括公开展示的特质和潜在的性格层面
2. 结合角色的行动、对话和故事中的表现来支持你的分析
3. 性格特点应简明扼要，但traits部分要提供详细解释和文本证据
4. 在description部分提供全面的角色概述
5. 在analysis部分深入分析角色的性格复杂性和故事弧
6. 提取角色在文本中的经典或代表性台词
7. 确保输出是合法的JSON格式
8. 分析应尽可能基于文本内容，避免过度推测
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
            
            # 调用API
            response = client.chat.completions.create(
                model=settings.OPENAI_API_MODEL,
                messages=messages,
                temperature=0.7,
                max_tokens=3000
            )
            
            # 获取响应内容
            content = response.choices[0].message.content
            logger.info("\n===角色性格分析原始响应===\n%s", content)
            
            # 提取JSON内容
            json_match = re.search(r'\{\s*"name".*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = content
            
            try:
                result = json.loads(json_str)
                logger.info(f"成功解析角色性格分析结果")
                return result
            except json.JSONDecodeError as je:
                logger.error(f"JSON解析错误: {str(je)}")
                # 尝试清理内容
                cleaned_content = OpenAIClient.clean_json_content(content)
                return json.loads(cleaned_content)
                
        except Exception as e:
            logger.error(f"角色性格分析失败: {str(e)}")
            raise
    
    @staticmethod
    def clean_json_content(content: str) -> str:
        """清理并修复JSON内容
        
        Args:
            content: 原始响应内容
            
        Returns:
            清理后的JSON字符串
        """
        # 移除包含"```json"和"```"的标记
        content = re.sub(r'```json\s*', '', content)
        content = re.sub(r'```\s*', '', content)
        
        # 移除开头可能的解释文本
        json_start = content.find('{')
        json_array_start = content.find('[')
        
        if json_start == -1 and json_array_start == -1:
            return content
            
        if json_start == -1:
            start_pos = json_array_start
        elif json_array_start == -1:
            start_pos = json_start
        else:
            start_pos = min(json_start, json_array_start)
            
        content = content[start_pos:]
        
        # 移除末尾可能的额外文本
        json_end = content.rfind('}')
        json_array_end = content.rfind(']')
        
        if json_end == -1 and json_array_end == -1:
            return content
            
        if json_end == -1:
            end_pos = json_array_end + 1
        elif json_array_end == -1:
            end_pos = json_end + 1
        else:
            end_pos = max(json_end, json_array_end) + 1
            
        content = content[:end_pos]
        
        return content
    
    @staticmethod
    def generate_mock_characters_data() -> List[Dict[str, Any]]:
        """生成模拟的角色分析数据（用于测试）"""
        return [
            {
                "name": "林黛玉",
                "alias": ["颦颦", "潇湘妃子"],
                "description": "贾府的表小姐，性格多愁善感，诗才出众，与贾宝玉青梅竹马。",
                "importance": 5
            },
            {
                "name": "贾宝玉",
                "alias": ["二爷", "天缘宝玉"],
                "description": "贾府嫡子，生性淡泊功名，重情重义，与林黛玉、薛宝钗都有感情纠葛。",
                "importance": 5
            },
            {
                "name": "薛宝钗",
                "alias": ["宝姐姐"],
                "description": "薛家千金，性格温婉端庄，世故圆滑，与贾宝玉有婚约。",
                "importance": 4
            }
        ]
    
    @staticmethod
    def generate_mock_character_personality() -> Dict[str, Any]:
        """生成模拟的角色性格分析数据（用于测试）"""
        return {
            "name": "林黛玉",
            "personality": ["敏感", "多愁善感", "才华横溢", "骄傲", "孤独"],
            "traits": [
                {
                    "trait": "敏感",
                    "description": "对周围环境和他人言行极为敏感",
                    "evidence": "每每因小事而伤心落泪"
                },
                {
                    "trait": "诗才出众",
                    "description": "天生的诗词天赋",
                    "evidence": "葬花吟等名作"
                }
            ],
            "description": "林黛玉是《红楼梦》中的女主角，贾母的外孙女，父母双亡后被接到贾府居住。她聪慧敏感，诗才出众，但体弱多病，性格孤傲。",
            "analysis": "林黛玉的性格复杂，表面娇弱但内心坚强，对贾宝玉有着深厚的感情。她的多愁善感部分源于自身处境，作为寄人篱下的孤女，时刻感到不安全感。",
            "quotes": [
                "一年三百六十日，风刀霜剑严相逼。",
                "花谢花飞花满天，红消香断有谁怜？"
            ]
        }

    @staticmethod
    async def extract_character_relationships_from_list(content: str, character_list: str) -> Dict[str, Any]:
        """从已知角色列表中提取角色之间的关系
        
        Args:
            content: 小说内容
            character_list: 角色名称列表，逗号分隔
            
        Returns:
            包含节点和边的字典
        """
        try:
            # 如果配置为使用模拟数据，直接返回
            if settings.USE_MOCK_DATA:
                logger.info("已配置使用模拟数据，跳过API调用")
                return OpenAIClient.generate_mock_relationship_data()
            
            system_prompt = """你是一位专业的文学分析师，专长于分析小说中角色关系网络。"""
            
            user_prompt = f"""分析小说内容，提取所有角色间的关系，特别关注：{character_list}

提取要求：
1. 全面分析所有角色关系，包括背景角色（如"姓阮的外乡铁匠"）
2. 特别关注以下关系类型：
   - 师徒关系（如刘羡阳和姚老头）
   - 交易关系（如锦衣少年与陈平安）
   - 社交、敌对、主仆、家族关系
3. 提供关系描述和文本证据
4. 为每个关系评估重要性（0.1-1.0）
5. 使用标准化的角色名称：
   - 确保"卖鱼中年人"和"卖鱼的中年人"等相似描述被识别为同一角色
   - 严格使用提供的角色列表中的准确名称
   - 对未命名角色，使用统一的描述格式

以JSON格式返回：
{{
  "edges": [
    {{
      "source_name": "角色A",
      "target_name": "角色B",
      "relation": "关系类型",
      "description": "关系描述与证据",
      "importance": 0.1-1.0
    }}
  ]
}}

重要提示：宁可多报关系也不要遗漏，返回纯JSON格式。

以下是小说内容:
{content[:70000]}"""  # 限制内容长度
            
            # 初始化客户端
            client = OpenAI(
                api_key=settings.OPENAI_API_KEY,
                base_url=settings.OPENAI_API_BASE
            )
            
            # 调用API
            response = client.chat.completions.create(
                model=settings.OPENAI_API_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            # 获取响应内容
            content = response.choices[0].message.content
            logger.info("\n===原始关系分析响应===\n%s", content)
            
            # 健壮的JSON解析
            try:
                # 尝试直接解析
                result = json.loads(content)
                logger.info(f"成功解析JSON响应，找到{len(result.get('edges', []))}个关系")
            except json.JSONDecodeError as e:
                logger.warning(f"直接JSON解析失败: {str(e)}，尝试清理响应内容")
                
                # 清理内容，移除可能的前缀说明
                cleaned_content = content
                prefixes = [
                    "好的，", "这是", "以下是", "根据文本，", 
                    "分析结果：", "人物关系如下：", "JSON格式如下：",
                    "```json", "```"
                ]
                for prefix in prefixes:
                    if cleaned_content.startswith(prefix):
                        cleaned_content = cleaned_content[len(prefix):].strip()
                
                # 尝试提取大括号内容
                try:
                    pattern = r'\{[\s\S]*\}'  # 匹配包括换行符在内的所有字符
                    match = re.search(pattern, cleaned_content)
                    if match:
                        result = json.loads(match.group())
                        logger.info(f"通过正则表达式提取并成功解析JSON，找到{len(result.get('edges', []))}个关系")
                    else:
                        # 如果找不到有效的JSON，返回空结果
                        logger.error("无法从响应中提取有效的JSON数据")
                        result = {"edges": []}
                except (json.JSONDecodeError, AttributeError) as e2:
                    logger.error(f"JSON提取和解析失败: {str(e2)}")
                    result = {"edges": []}
            
            # 确保结果包含必要的字段
            if "edges" not in result:
                result["edges"] = []
            
            return result
        except Exception as e:
            logger.error(f"OpenAI API提取角色关系失败: {str(e)}")
            return {"edges": []} 