from sqlalchemy import create_engine, Column, Integer, Table, MetaData, text
from app.core.config import settings

def migrate():
    """
    添加地点重要性字段的迁移
    """
    # 创建引擎和元数据
    engine = create_engine(settings.SQLALCHEMY_DATABASE_URI)
    metadata = MetaData()
    
    # 绑定locations表
    locations = Table('locations', metadata, autoload_with=engine)
    
    # 检查字段是否已存在
    if 'importance' not in locations.columns:
        # 添加importance字段
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE locations ADD COLUMN importance INTEGER DEFAULT 1"))
            conn.commit()
            print("已成功添加locations.importance字段")
    else:
        print("locations.importance字段已存在，无需添加")

if __name__ == "__main__":
    migrate() 