#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path
import logging
from dotenv import load_dotenv

# 设置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载.env文件
env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)

# 获取环境变量或使用默认值
API_KEY = os.environ.get('OPENAI_API_KEY', 'sk-icxXNDdO3E6Y6FO6l8A7uuCu6hs4HE6XGHjkG5aCq6QjQZ8k')
API_BASE = os.environ.get('OPENAI_API_BASE', 'https://api.lkeap.cloud.tencent.com/v1')
API_MODEL = os.environ.get('OPENAI_API_MODEL', 'deepseek-r1')

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
    
    # 执行简单测试
    logger.info("发送测试请求：'9.9和9.11谁大'")
    completion = client.chat.completions.create(
        model=API_MODEL,
        messages=[
            {'role': 'user', 'content': '9.9和9.11谁大'}
        ]
    )
    
    # 输出思考过程
    print("\n===思考过程===")
    try:
        reasoning = completion.choices[0].message.reasoning_content
        if reasoning:
            print(reasoning)
        else:
            print("无思考过程输出（reasoning_content为空）")
    except AttributeError:
        print("没有找到reasoning_content字段，这可能是因为所使用的模型不支持此特性")
    
    # 输出最终答案
    print("\n===最终答案===")
    print(completion.choices[0].message.content)
    
    # 输出完整的响应对象，用于调试
    print("\n===响应结构===")
    print(f"响应对象类型: {type(completion)}")
    print(f"choices[0].message类型: {type(completion.choices[0].message)}")
    print(f"message的可用属性: {dir(completion.choices[0].message)}")
    
    logger.info("测试完成")

except ImportError:
    logger.error("无法导入OpenAI模块，请确保已安装最新版本: pip install openai>=1.0.0")
    sys.exit(1)
except Exception as e:
    logger.error(f"测试失败: {str(e)}")
    import traceback
    traceback.print_exc()
    sys.exit(1) 