from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from app.config import get_settings

settings = get_settings()

# 创建异步引擎，将PostgreSQL URL转换为异步版本
engine = create_async_engine(
    str(settings.PG_URL).replace("postgresql://", "postgresql+asyncpg://"),
    pool_size=settings.PG_POOL_MAX,
    echo=settings.LOG_LEVEL == "debug",
)

# 创建异步会话工厂
SessionLocal = sessionmaker(
    engine, 
    class_=AsyncSession, 
    expire_on_commit=False
)

# 创建基类用于ORM模型
Base = declarative_base()

# 提供异步数据库会话的依赖
async def get_db() -> AsyncSession:
    """获取数据库会话的异步上下文管理器"""
    db = SessionLocal()
    try:
        yield db
    finally:
        await db.close() 