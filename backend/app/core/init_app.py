import logging
from fastapi import FastAPI
from pymilvus import connections, utility, Collection, CollectionSchema, FieldSchema, DataType

from app.core.config import settings

logger = logging.getLogger(__name__)

def init_app(app: FastAPI) -> None:
    """
    初始化应用
    """
    init_logger()
    if not settings.DEBUG:
        init_vector_db()
    else:
        logger.info("开发模式：跳过向量数据库初始化")

def init_logger():
    """
    初始化日志配置
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    )
    logger.info("日志系统初始化完成")

def init_vector_db():
    """
    初始化向量数据库连接和集合
    """
    try:
        # 连接到Milvus
        connections.connect("default", host=settings.MILVUS_HOST, port=settings.MILVUS_PORT)
        logger.info(f"成功连接到Milvus服务器: {settings.MILVUS_HOST}:{settings.MILVUS_PORT}")
        
        # 检查并创建集合
        create_novel_collection()
        
    except Exception as e:
        logger.error(f"向量数据库初始化失败: {str(e)}")
        # 在开发环境不阻止应用启动
        if not settings.DEBUG:
            raise

def create_novel_collection():
    """创建小说文本向量集合"""
    collection_name = "novel_chunks"
    
    # 如果集合已存在就跳过
    if utility.has_collection(collection_name):
        logger.info(f"集合 {collection_name} 已存在")
        return
    
    # 定义集合字段
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="chunk_id", dtype=DataType.INT64),        # 数据库中的chunk_id
        FieldSchema(name="novel_id", dtype=DataType.INT64),        # 小说ID
        FieldSchema(name="chapter_id", dtype=DataType.INT64),      # 章节ID
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=settings.VECTOR_DIMENSION)  # 向量
    ]
    
    # 创建集合模式
    schema = CollectionSchema(fields=fields, description="小说文本片段向量集合")
    
    # 创建集合
    collection = Collection(name=collection_name, schema=schema)
    
    # 创建索引
    index_params = {
        "metric_type": "COSINE",  # 余弦相似度
        "index_type": "HNSW",     # 高效的近似最近邻索引
        "params": {"M": 8, "efConstruction": 64}
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    
    logger.info(f"成功创建集合 {collection_name} 及其索引") 