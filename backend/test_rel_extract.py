#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path
import logging
import json
import re
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载.env文件
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

# 获取环境变量
API_KEY = os.environ.get('OPENAI_API_KEY')
API_BASE = os.environ.get('OPENAI_API_BASE')
API_MODEL = os.environ.get('OPENAI_API_MODEL')

try:
    from openai import OpenAI
    logger.info("使用新版本OpenAI API")
    
    # 检查API密钥是否设置
    if not API_KEY:
        logger.error("未设置OpenAI API密钥")
        sys.exit(1)
    
    logger.info(f"API基础URL: {API_BASE}")
    logger.info(f"API模型: {API_MODEL}")
    logger.info(f"API密钥: {API_KEY[:4]}...{API_KEY[-4:]}")
    
    # 初始化客户端
    client = OpenAI(
        api_key=API_KEY,
        base_url=API_BASE,
    )
    
    # 测试文本
    test_text = """
    林惜是青云门的天才弟子，精通炼丹之术。她与同门师兄秦煜青梅竹马，两人自小一起长大。
    秦煜是掌门王长老的得意弟子，剑术超群。他的师兄李寒对他亦师亦友，常常指导他修炼。
    某日，神秘的黑袍人突然现身青云门，与秦煜大战一场，原来他与秦煜有着不共戴天之仇。
    隐世高人古尘见林惜资质非凡，收她为徒。原来古尘与王长老是多年故交，但与黑袍人却是曾经的同门，如今势不两立。
    林惜的闺蜜赵敏一直支持着她，两人情同姐妹。
    """
    
    # 系统提示词
    system_prompt = """
    你的任务是从下面提供的小说文本中提取主要人物及其关系。
    请注意以下要求：
    1. 提取主要角色：识别文本中的主要人物，包括姓名、别名和简短描述。
    2. 分析关系：确定角色之间的关系类型（如亲属、朋友、恋人、师徒、敌人）。
    3. 输出必须是以下指定的JSON格式，其中包含nodes（人物节点）和edges（关系连接）。
    4. 请确保返回有效的JSON格式，不要包含任何额外的文本或解释。
    
    输出格式示例:
    {
        "nodes": [
            {"id": 1, "name": "林惜", "description": "女主角，青云门弟子", "importance": 5},
            {"id": 2, "name": "秦煜", "description": "男主角，元阳派掌门", "importance": 5}
        ],
        "edges": [
            {"source_id": 1, "target_id": 2, "source_name": "林惜", "target_name": "秦煜", "relation": "恋人", "description": "两人相恋多年", "importance": 5}
        ]
    }
    """
    
    # 执行API调用
    logger.info("发送测试请求...")
    completion = client.chat.completions.create(
        model=API_MODEL,
        messages=[
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': f"请从以下文本中提取人物关系：\n\n{test_text}"}
        ],
        temperature=0.2
    )
    
    # 获取响应内容
    content = completion.choices[0].message.content
    logger.info(f"\n===原始响应===\n{content}")
    
    # 尝试提取JSON
    def extract_json(text):
        # 方法1：直接尝试解析整个内容
        try:
            data = json.loads(text)
            if "nodes" in data and "edges" in data:
                logger.info("方法1成功：直接解析整个内容")
                return data
        except json.JSONDecodeError:
            pass
        
        # 方法2：查找第一个{和最后一个}之间的内容
        try:
            start = text.find('{')
            end = text.rfind('}') + 1
            if start >= 0 and end > start:
                json_str = text[start:end]
                data = json.loads(json_str)
                if "nodes" in data and "edges" in data:
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
                    if "nodes" in data and "edges" in data:
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
        logger.info("\n===解析后的数据===")
        logger.info(f"节点数量: {len(parsed_data['nodes'])}")
        logger.info(f"关系数量: {len(parsed_data['edges'])}")
        logger.info("\n===完整数据===")
        print(json.dumps(parsed_data, ensure_ascii=False, indent=2))
    else:
        logger.error("无法从响应中提取有效的JSON数据")
    
except ImportError:
    logger.error("无法导入OpenAI模块，请确保已安装最新版本: pip install openai>=1.0.0")
    sys.exit(1)
except Exception as e:
    logger.error(f"测试失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 