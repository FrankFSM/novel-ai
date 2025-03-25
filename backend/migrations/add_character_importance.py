from sqlalchemy import create_engine, Column, Integer, Table, MetaData, text
from app.core.config import settings

def migrate():
    """
    添加角色重要性字段的迁移
    """
    # 创建引擎和元数据
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    metadata = MetaData()
    
    # 绑定characters表
    characters = Table('characters', metadata, autoload_with=engine)
    
    # 检查字段是否已存在
    if 'importance' not in characters.columns:
        # 添加importance字段
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE characters ADD COLUMN importance INTEGER DEFAULT 1"))
            conn.commit()
            print("已成功添加characters.importance字段")
    else:
        print("characters.importance字段已存在，无需添加")

if __name__ == "__main__":
    migrate() 