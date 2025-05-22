from pydantic import BaseSettings, PostgresDsn
from typing import Optional, Literal


class Settings(BaseSettings):
    """
    应用程序配置设置。
    使用环境变量进行配置，环境变量前缀为KOMPANION_。
    """
    # 应用设置
    APP_NAME: str = "kompanion"
    VERSION: str = "dev"
    
    # 认证设置
    AUTH_USERNAME: str
    AUTH_PASSWORD: str
    AUTH_STORAGE: Literal["postgres", "memory"] = "postgres"
    
    # HTTP设置
    HTTP_PORT: int = 8080
    
    # 日志设置
    LOG_LEVEL: Literal["debug", "info", "error"] = "info"
    
    # PostgreSQL设置
    PG_URL: PostgresDsn
    PG_POOL_MAX: int = 2
    
    # 书籍存储设置
    BSTORAGE_TYPE: Literal["postgres", "memory", "filesystem"] = "postgres"
    BSTORAGE_PATH: Optional[str] = None
    
    class Config:
        """配置元数据"""
        env_prefix = "KOMPANION_"
        env_file = ".env"
        case_sensitive = True


# 创建全局配置实例
def get_settings() -> Settings:
    """获取应用配置实例"""
    return Settings() 