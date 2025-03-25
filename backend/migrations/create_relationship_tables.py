"""
创建关系网络分析结果存储表
"""
import logging
import sys
import os
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from sqlalchemy.orm import sessionmaker
import sqlite3

# 添加项目根目录到路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

try:
    from app.core.config import settings
    # 尝试从settings获取数据库URL
    DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI
except (ImportError, AttributeError):
    # 如果无法导入或找不到属性，使用默认SQLite数据库
    DATABASE_URL = "sqlite:///novel_ai.db"

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 连接数据库
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# 定义表结构
class RelationshipGraph(Base):
    """关系网络分析结果表"""
    __tablename__ = "relationship_graphs"
    
    id = Column(Integer, primary_key=True, index=True)
    novel_id = Column(Integer, ForeignKey("novels.id", ondelete="CASCADE"), nullable=False)
    character_id = Column(Integer, ForeignKey("characters.id", ondelete="CASCADE"), nullable=True)
    depth = Column(Integer, default=1)
    
    # 存储节点数据
    nodes = Column(JSON)
    
    # 创建和更新时间
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class RelationshipEdge(Base):
    """关系网络边数据表"""
    __tablename__ = "relationship_edges"
    
    id = Column(Integer, primary_key=True, index=True)
    graph_id = Column(Integer, ForeignKey("relationship_graphs.id", ondelete="CASCADE"), nullable=False)
    
    source_id = Column(Integer, nullable=False)
    target_id = Column(Integer, nullable=False)
    source_name = Column(String, nullable=False)
    target_name = Column(String, nullable=False)
    relation = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    importance = Column(Float, default=1.0)

def create_tables():
    """创建表"""
    try:
        # 创建表
        Base.metadata.create_all(bind=engine)
        logger.info("创建关系图存储表完成")
    except Exception as e:
        logger.error(f"创建表失败: {str(e)}")

if __name__ == "__main__":
    create_tables() 