import sqlite3
import logging
import json
import sys
import os

# 获取当前脚本所在目录的上一级目录路径（即项目根目录）
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate():
    """
    迁移脚本：向characters表添加appearances列
    
    将添加的列类型为JSON，用于存储角色出现的章节ID列表
    """
    try:
        # 连接数据库
        conn = sqlite3.connect(settings.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", ""))
        cursor = conn.cursor()
        logger.info("已连接到数据库")
        
        # 检查appearances列是否已存在
        cursor.execute("PRAGMA table_info(characters)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if "appearances" not in column_names:
            # 添加appearances列到characters表
            cursor.execute("ALTER TABLE characters ADD COLUMN appearances TEXT")
            logger.info("已成功添加appearances列到characters表")
            
            # 更新所有现有记录，设置appearances为空数组
            cursor.execute("UPDATE characters SET appearances = ?", (json.dumps([]),))
            logger.info(f"已更新{cursor.rowcount}条记录的appearances值")
            
            # 提交事务
            conn.commit()
            logger.info("事务已提交")
        else:
            logger.info("appearances列已存在，无需添加")
        
    except Exception as e:
        logger.error(f"迁移失败: {str(e)}")
        # 回滚事务
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        # 关闭数据库连接
        if 'conn' in locals():
            conn.close()
            logger.info("数据库连接已关闭")

if __name__ == "__main__":
    logger.info("开始运行迁移脚本: add_character_appearances")
    migrate()
    logger.info("迁移脚本执行完成") 