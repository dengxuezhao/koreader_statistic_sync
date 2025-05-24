import logging
from fastapi import APIRouter, Depends, Request, Response, HTTPException, status
from typing import Annotated, List, Optional
import base64
from datetime import datetime
import os

from app.dependencies import get_auth_service
from app.service import AuthService
from app.api.opds.opds import (
    Entry, build_feed, books_to_entries, form_navigation_links,
    ATOM_TIME_FORMAT, DIR_MIME
)


# 创建路由器
router = APIRouter()
logger = logging.getLogger(__name__)


# OPDS基本认证中间件
async def basic_auth(
    request: Request, 
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> str:
    """
    OPDS基本认证中间件
    
    Args:
        request: FastAPI请求对象
        auth_service: 认证服务实例
        
    Returns:
        str: 设备名称或用户名，如果认证失败则抛出HTTPException
    """
    # 获取Authorization头
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        # 如果没有Authorization头，返回401
        logger.debug("OPDS Basic Auth: Missing or invalid Authorization header.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证",
            headers={"WWW-Authenticate": "Basic realm=\"KOmpanion OPDS\""}
        )
    
    # 解码Basic认证
    identifier: str = ""
    password: str = ""
    try:
        auth_decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
        identifier, password = auth_decoded.split(":", 1)
    except Exception as e:
        logger.error(f"解码Basic认证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证格式无效",
            headers={"WWW-Authenticate": "Basic realm=\"KOmpanion OPDS\""}
        )
    
    # 尝试设备认证 (KOReader OPDS often uses device credentials, sends plain password)
    logger.debug(f"OPDS Basic Auth: Attempting device auth for identifier: {identifier}")
    if await auth_service.check_device_password(identifier, password, plain=False):
        logger.info(f"OPDS authentication successful for device: {identifier}")
        return identifier
    
    # 尝试用户认证 (if device auth fails)
    logger.debug(f"OPDS Basic Auth: Device auth failed for {identifier}, attempting user auth.")
    try:
        user = await auth_service.user_repo.get_user_by_username(identifier)
        if user and auth_service._verify_password(password, user.hashed_password):
            logger.info(f"OPDS authentication successful for user: {identifier}")
            return identifier
    except Exception as e: # Catch potential errors from user_repo.get_user_by_username if user not found etc.
        logger.debug(f"OPDS Basic Auth: User repo lookup or password verification failed for user {identifier}: {str(e)}")
        pass # Continue to final failure if this path doesn't succeed
    
    # 如果都认证失败，返回401
    logger.warning(f"OPDS authentication failed for identifier: {identifier}")
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="用户名或密码不正确",
        headers={"WWW-Authenticate": "Basic realm=\"KOmpanion OPDS\""}
    )


@router.get("/")
async def list_shelves(
    request: Request,
    device_name: str = Depends(basic_auth)
):
    """
    列出书架
    
    这是OPDS的根目录，列出可用的书架。
    """
    logger.info(f"OPDS列出书架请求: 设备={device_name}")
    
    # 创建书架条目
    shelves = [
        Entry(
            id="urn:kompanion:newest",
            title="最新添加",
            updated=datetime.now().strftime(ATOM_TIME_FORMAT),
            links=[
                {
                    "href": "/opds/newest/",
                    "type": "application/atom+xml;type=feed;profile=opds-catalog",
                    "rel": "subsection"
                }
            ]
        )
    ]
    
    # 构建Feed
    feed = build_feed(
        id="urn:kompanion:main",
        title="KOmpanion书库",
        href="/opds",
        entries=shelves
    )
    
    # 返回XML响应
    return Response(
        content=feed.to_xml(),
        media_type="application/atom+xml;profile=opds-catalog"
    )


@router.get("/newest/")
async def list_newest(
    request: Request,
    book_shelf: Annotated[BookShelf, Depends(get_book_shelf)],
    device_name: str = Depends(basic_auth),
    page: int = 1
):
    """
    列出最新添加的书籍
    
    这是OPDS的书籍列表，按添加时间排序。
    """
    logger.info(f"OPDS列出最新书籍请求: 设备={device_name}, 页码={page}")
    
    # 获取书籍列表
    books = await book_shelf.list_books(None, "created_at", "desc", page, 10)
    
    # 构建基础URL
    base_url = "/opds/newest/"
    
    # 将书籍转换为条目
    entries = books_to_entries(books.items)
    
    # 构建导航链接
    nav_links = form_navigation_links(base_url, books)
    
    # 构建Feed
    feed = build_feed(
        id="urn:kompanion:newest",
        title="最新添加的书籍",
        href=base_url,
        entries=entries,
        additional_links=nav_links
    )
    
    # 返回XML响应
    return Response(
        content=feed.to_xml(),
        media_type="application/atom+xml;profile=opds-catalog"
    )


@router.get("/book/{book_id}/download")
async def download_book(
    book_id: str,
    book_shelf: Annotated[BookShelf, Depends(get_book_shelf)],
    device_name: str = Depends(basic_auth)
):
    """
    下载书籍
    
    通过OPDS下载书籍文件。
    """
    logger.info(f"OPDS下载书籍请求: 设备={device_name}, 书籍ID={book_id}")
    
    try:
        # 获取书籍
        book, temp_file_path = await book_shelf.download_book(None, book_id)
        
        # 返回文件
        return Response(
            content=open(temp_file_path, "rb").read(),
            media_type=book.mime_type(),
            headers={"Content-Disposition": f"attachment; filename={book.filename()}"}
        )
    except Exception as e:
        logger.error(f"下载书籍失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到书籍: {book_id}"
        )


@router.get("/book/{book_id}/cover")
async def view_book_cover(
    book_id: str,
    book_shelf: Annotated[BookShelf, Depends(get_book_shelf)],
    device_name: str = Depends(basic_auth)
):
    """
    查看书籍封面
    
    通过OPDS查看书籍封面。
    """
    logger.info(f"OPDS查看书籍封面请求: 设备={device_name}, 书籍ID={book_id}")
    
    try:
        # 获取封面
        cover_path = await book_shelf.view_cover(None, book_id)
        
        # 返回文件
        return Response(
            content=open(cover_path, "rb").read(),
            media_type="image/jpeg"
        )
    except Exception as e:
        logger.error(f"查看书籍封面失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到书籍封面: {book_id}"
        ) 