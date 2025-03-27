from sqlalchemy import create_engine, Table, MetaData, text
from app.core.config import settings
import datetime

def migrate():
    """
    添加角色时间戳字段的迁移
    """
    # 创建引擎和元数据
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    metadata = MetaData()
    
    # 绑定characters表
    characters = Table('characters', metadata, autoload_with=engine)
    
    # 检查字段是否已存在
    with engine.connect() as conn:
        # 获取数据库类型
        dialect = engine.dialect.name
        
        if dialect == 'sqlite':
            # SQLite特殊处理
            # 添加created_at字段（如果不存在）
            if 'created_at' not in characters.columns:
                # SQLite中使用固定时间戳作为默认值
                current_time = datetime.datetime.now().isoformat()
                conn.execute(text(f"ALTER TABLE characters ADD COLUMN created_at TEXT DEFAULT '{current_time}'"))
                print("已成功添加characters.created_at字段")
            else:
                print("characters.created_at字段已存在，无需添加")
            
            # 添加updated_at字段（如果不存在）
            if 'updated_at' not in characters.columns:
                conn.execute(text("ALTER TABLE characters ADD COLUMN updated_at TEXT"))
                print("已成功添加characters.updated_at字段")
            else:
                print("characters.updated_at字段已存在，无需添加")
        else:
            # PostgreSQL/MySQL等处理
            # 添加created_at字段（如果不存在）
            if 'created_at' not in characters.columns:
                conn.execute(text("ALTER TABLE characters ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP"))
                print("已成功添加characters.created_at字段")
            else:
                print("characters.created_at字段已存在，无需添加")
            
            # 添加updated_at字段（如果不存在）
            if 'updated_at' not in characters.columns:
                conn.execute(text("ALTER TABLE characters ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE"))
                print("已成功添加characters.updated_at字段")
            else:
                print("characters.updated_at字段已存在，无需添加")
        
        # 添加image_url字段（如果不存在）
        if 'image_url' not in characters.columns:
            conn.execute(text("ALTER TABLE characters ADD COLUMN image_url VARCHAR(255)"))
            print("已成功添加characters.image_url字段")
        else:
            print("characters.image_url字段已存在，无需添加")
            
        conn.commit()
    
    print("迁移完成")

if __name__ == "__main__":
    migrate() 