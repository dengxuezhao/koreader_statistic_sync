from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import Settings
from app.storage.base import Storage
from app.storage.postgres import PostgresStorage
from app.storage.filesystem import FilesystemStorage
from app.storage.memory import MemoryStorage


async def get_storage(storage_type: str, path: Optional[str], db: AsyncSession) -> Storage:
    """
    根据配置创建适当的存储实现。
    
    Args:
        storage_type: 存储类型 ("postgres", "filesystem", "memory")
        path: 文件系统存储的基础路径，仅当storage_type为"filesystem"时使用
        db: SQLAlchemy异步会话，仅当storage_type为"postgres"时使用
        
    Returns:
        存储实现实例
        
    Raises:
        ValueError: 当存储类型无效时抛出
    """
    if storage_type == "postgres":
        return PostgresStorage(db)
    elif storage_type == "filesystem":
        if not path:
            raise ValueError("Path must be specified for filesystem storage")
        return FilesystemStorage(path)
    elif storage_type == "memory":
        return MemoryStorage()
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")


__all__ = ["get_storage", "Storage", "PostgresStorage", "FilesystemStorage", "MemoryStorage"]
