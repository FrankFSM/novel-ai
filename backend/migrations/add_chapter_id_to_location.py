import sqlite3
import logging
import os
import sys

# 获取当前脚本所在目录的上一级目录路径（即项目根目录）
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def migrate():
    """
    迁移脚本：向locations表添加chapter_id列
    """
    try:
        # 连接数据库
        db_path = settings.SQLALCHEMY_DATABASE_URI.replace("sqlite:///", "")
        logger.info(f"连接到数据库: {db_path}")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查chapter_id列是否已存在
        cursor.execute("PRAGMA table_info(locations)")
        columns = cursor.fetchall()
        column_names = [column[1] for column in columns]
        
        if "chapter_id" not in column_names:
            logger.info("开始添加chapter_id列到locations表")
            
            # SQLite不支持直接添加外键列，所以我们需要：
            # 1. 创建一个新表，包含新的列结构
            # 2. 复制所有数据
            # 3. 删除旧表
            # 4. 重命名新表
            
            # 1. 创建一个新表，包含新的列结构
            cursor.execute("""
            CREATE TABLE locations_new (
                id INTEGER PRIMARY KEY,
                novel_id INTEGER NOT NULL,
                chapter_id INTEGER,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                parent_id INTEGER,
                importance INTEGER,
                FOREIGN KEY(novel_id) REFERENCES novels(id),
                FOREIGN KEY(chapter_id) REFERENCES chapters(id),
                FOREIGN KEY(parent_id) REFERENCES locations(id)
            )
            """)
            
            # 2. 复制所有数据
            cursor.execute("""
            INSERT INTO locations_new (id, novel_id, name, description, parent_id, importance)
            SELECT id, novel_id, name, description, parent_id, importance FROM locations
            """)
            
            # 3. 删除旧表
            cursor.execute("DROP TABLE locations")
            
            # 4. 重命名新表
            cursor.execute("ALTER TABLE locations_new RENAME TO locations")
            
            # 5. 重新创建索引
            cursor.execute("CREATE INDEX ix_locations_name ON locations (name)")
            cursor.execute("CREATE INDEX ix_locations_novel_id ON locations (novel_id)")
            
            # 提交事务
            conn.commit()
            logger.info("成功添加chapter_id列到locations表，并保留了原有数据")
        else:
            logger.info("chapter_id列已存在，无需添加")
            
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
    logger.info("开始运行迁移脚本: add_chapter_id_to_location")
    migrate()
    logger.info("迁移脚本执行完成") 