from pydantic import BaseSettings
import os
from typing import Optional, Dict, Any, List

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "长篇小说智能分析系统"
    
    # 安全配置
    SECRET_KEY: str = "YOUR_SECRET_KEY_HERE"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7天
    
    # 数据库配置
    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "localhost")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "novel_ai")
    SQLALCHEMY_DATABASE_URI: Optional[str] = None
    
    # Redis配置
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", 6379))
    
    # Milvus配置
    MILVUS_HOST: str = os.getenv("MILVUS_HOST", "localhost")
    MILVUS_PORT: int = int(os.getenv("MILVUS_PORT", 19530))
    
    # OpenAI配置
    OPENAI_API_KEY: str = "sk-icxXNDdO3E6Y6FO6l8A7uuCu6hs4HE6XGHjkG5aCq6QjQZ8k"
    OPENAI_API_BASE: str = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
    OPENAI_API_MODEL: str = "deepseek-r1"
    
    # 小说处理配置
    CHUNK_SIZE: int = 1000  # 文本分块大小
    CHUNK_OVERLAP: int = 200  # 分块重叠大小
    
    # 向量配置
    VECTOR_DIMENSION: int = 1536  # OpenAI embedding维度
    
    # 开发模式配置
    DEBUG: bool = True
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **data: Any):
        super().__init__(**data)
        # 在开发环境中使用SQLite
        if self.DEBUG:
            self.SQLALCHEMY_DATABASE_URI = "sqlite:///./novel_ai.db"
        else:
            self.SQLALCHEMY_DATABASE_URI = f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"

settings = Settings() 