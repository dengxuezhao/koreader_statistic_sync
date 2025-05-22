from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from functools import lru_cache
from typing import Annotated, TypeAlias

from app.config import Settings, get_settings
from app.database import get_db
from app.storage import Storage, FileSystemStorage, MemoryStorage
from app.repository import (
    UserRepo, UserDatabaseRepo, MemoryUserRepo,
    BookRepo, BookDatabaseRepo, MemoryBookRepo,
    ProgressRepo, ProgressDatabaseRepo, MemoryProgressRepo
)
from app.service import AuthService, ProgressSync, ReadingStats
from app.service.book_shelf import BookShelf

# 类型别名以增强可读性
DBSession: TypeAlias = Annotated[AsyncSession, Depends(get_db)]
AppSettings: TypeAlias = Annotated[Settings, Depends(get_settings)]

# 存储依赖
@lru_cache()
async def get_storage(
    db: DBSession = Depends(),
    settings: AppSettings = Depends()
) -> Storage:
    """根据配置获取适当的存储实现。"""
    if settings.BSTORAGE_TYPE == "fs":
        return FileSystemStorage(settings.STORAGE_DIR)
    return MemoryStorage()

@lru_cache()
async def get_user_repo(
    db: DBSession = Depends(),
    settings: AppSettings = Depends()
) -> UserRepo:
    """根据配置获取用户仓库实例。"""
    if settings.AUTH_STORAGE == "pg":
        return UserDatabaseRepo(db)
    return MemoryUserRepo()

@lru_cache()
async def get_auth_service(
    user_repo: UserRepo = Depends(get_user_repo),
) -> AuthService:
    """获取认证服务实例。"""
    return AuthService(user_repo)

@lru_cache()
async def get_book_shelf(
    db: DBSession = Depends(), 
    settings: AppSettings = Depends(),
    storage: Storage = Depends(get_storage),
    book_repo: BookRepo = Depends(get_book_repo)
) -> BookShelf:
    """获取书架服务实例。"""
    return BookShelf(book_repo=book_repo, storage=storage)

@lru_cache()
async def get_book_repo(
    db: DBSession = Depends(),
    settings: AppSettings = Depends()
) -> BookRepo:
    """根据配置获取书籍仓库实例。"""
    if settings.BSTORAGE_TYPE == "pg":
        return BookDatabaseRepo(db)
    return MemoryBookRepo()

@lru_cache()
async def get_progress_repo(
    db: DBSession = Depends(),
    settings: AppSettings = Depends()
) -> ProgressRepo:
    """根据配置获取进度仓库实例。"""
    if settings.BSTORAGE_TYPE == "pg":
        return ProgressDatabaseRepo(db)
    return MemoryProgressRepo()

@lru_cache()
async def get_progress_sync(
    progress_repo: ProgressRepo = Depends(get_progress_repo)
) -> ProgressSync:
    """获取进度同步服务实例。"""
    return ProgressSync(progress_repo)

@lru_cache()
async def get_reading_stats(
    storage: Storage = Depends(get_storage)
) -> ReadingStats:
    """获取阅读统计服务实例。"""
    return ReadingStats(storage) 