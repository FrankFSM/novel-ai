import sqlite3
import os
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 数据库文件路径
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "novel_ai.db")

def update_character_table():
    """更新characters表结构，添加chapter_id列并删除appearances列"""
    try:
        # 连接数据库
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        logger.info(f"已连接到数据库: {DB_PATH}")
        
        # 获取characters表结构
        cursor.execute("PRAGMA table_info(characters)")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        # 检查chapter_id列是否已存在
        if "chapter_id" not in column_names:
            # 添加chapter_id列
            cursor.execute("ALTER TABLE characters ADD COLUMN chapter_id INTEGER")
            logger.info("已添加chapter_id列到characters表")
        else:
            logger.info("chapter_id列已存在")
        
        # 检查appearances列是否存在
        if "appearances" in column_names:
            # 在SQLite中，无法直接删除列，需要重建表
            # 1. 创建临时表
            cursor.execute("""
            CREATE TABLE characters_temp (
                id INTEGER PRIMARY KEY,
                novel_id INTEGER NOT NULL,
                chapter_id INTEGER,
                name VARCHAR(100) NOT NULL,
                alias JSON,
                description TEXT,
                first_appearance INTEGER,
                importance INTEGER,
                image_url VARCHAR(255),
                created_at TIMESTAMP,
                updated_at TIMESTAMP,
                FOREIGN KEY(novel_id) REFERENCES novels(id),
                FOREIGN KEY(chapter_id) REFERENCES chapters(id),
                FOREIGN KEY(first_appearance) REFERENCES chapters(id)
            )
            """)
            
            # 2. 复制数据（排除appearances列）
            cursor.execute("""
            INSERT INTO characters_temp 
            SELECT id, novel_id, chapter_id, name, alias, description, first_appearance, 
                   importance, image_url, created_at, updated_at
            FROM characters
            """)
            
            # 3. 删除原表
            cursor.execute("DROP TABLE characters")
            
            # 4. 重命名临时表
            cursor.execute("ALTER TABLE characters_temp RENAME TO characters")
            
            # 5. 创建索引
            cursor.execute("CREATE INDEX ix_characters_name ON characters (name)")
            cursor.execute("CREATE INDEX ix_characters_novel_id ON characters (novel_id)")
            
            logger.info("已重建characters表，删除了appearances列")
        else:
            logger.info("appearances列不存在，无需删除")
        
        # 提交更改
        conn.commit()
        logger.info("数据库更改已提交")
    
    except Exception as e:
        logger.error(f"更新characters表失败: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'conn' in locals():
            conn.close()
            logger.info("数据库连接已关闭")

if __name__ == "__main__":
    logger.info("开始更新characters表...")
    update_character_table()
    logger.info("characters表更新完成") 