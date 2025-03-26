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
    初始化日志配置，添加彩色日志支持
    """
    # 颜色代码常量
    RESET = "\033[0m"
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    BOLD = "\033[1m"
    
    # 为不同级别定义颜色
    class ColoredFormatter(logging.Formatter):
        FORMATS = {
            logging.DEBUG: BLUE + "%(asctime)s - %(name)s - " + BOLD + "%(levelname)s" + RESET + BLUE + " - %(message)s" + RESET,
            logging.INFO: GREEN + "%(asctime)s - %(name)s - " + BOLD + "%(levelname)s" + RESET + GREEN + " - %(message)s" + RESET,
            logging.WARNING: YELLOW + "%(asctime)s - %(name)s - " + BOLD + "%(levelname)s" + RESET + YELLOW + " - %(message)s" + RESET,
            logging.ERROR: RED + "%(asctime)s - %(name)s - " + BOLD + "%(levelname)s" + RESET + RED + " - %(message)s" + RESET,
            logging.CRITICAL: MAGENTA + BOLD + "%(asctime)s - %(name)s - %(levelname)s - %(message)s" + RESET
        }

        def format(self, record):
            log_fmt = self.FORMATS.get(record.levelno)
            formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
            return formatter.format(record)
    
    # 创建并配置控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(ColoredFormatter())
    
    # 配置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    
    # 移除现有处理器（如果有）
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # 添加新的处理器
    root_logger.addHandler(console_handler)
    
    # 为常用模块配置日志级别
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)  # 减少SQL日志
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("fastapi").setLevel(logging.INFO)
    
    logger.info("彩色日志系统初始化完成")

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