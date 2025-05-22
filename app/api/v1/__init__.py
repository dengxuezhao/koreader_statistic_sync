from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.books import router as books_router
from app.api.v1.progress import router as progress_router
from app.api.v1.stats import router as stats_router

# 创建API v1版本路由器
api_router = APIRouter(prefix="/api/v1")

# 添加认证路由
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["认证"]
)

# 添加书籍路由
api_router.include_router(
    books_router,
    prefix="/books",
    tags=["书籍管理"]
)

# 添加进度同步路由
api_router.include_router(
    progress_router,
    prefix="/progress",
    tags=["进度同步"]
)

# 添加阅读统计路由
api_router.include_router(
    stats_router,
    prefix="/stats",
    tags=["阅读统计"]
)

__all__ = ["api_router"]
