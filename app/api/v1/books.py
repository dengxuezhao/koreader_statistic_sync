from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status, Response, Request
from fastapi.responses import FileResponse, JSONResponse
from typing import Annotated, Optional, List, Dict, Any
import tempfile
import os
import logging
from contextlib import asynccontextmanager
import shutil

from app.dependencies import get_book_shelf, get_auth_service
from app.service.book_shelf import BookShelf
from app.entity.book import BookResponse, BookUpdate, BookAlreadyExistsError, Book
from app.service import get_current_user

router = APIRouter()
logger = logging.getLogger(__name__)

@asynccontextmanager
async def save_upload_file(upload_file: UploadFile):
    """临时保存上传的文件"""
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # 读取上传的文件并写入临时文件
            content = await upload_file.read()
            temp_file.write(content)
            temp_path = temp_file.name
        yield temp_path
    finally:
        # 清理临时文件
        if os.path.exists(temp_path):
            os.unlink(temp_path)

@router.post("/")
async def upload_book(
    file: UploadFile = File(...),
    request: Request = None,
    book_shelf: Annotated[BookShelf, Depends(get_book_shelf)] = None,
    user_id: str = Depends(get_current_user)
):
    """
    上传一本书
    
    Args:
        file: 电子书文件
        user_id: 用户ID
        book_shelf: 书架服务
        
    Returns:
        JSONResponse: 上传成功信息
    """
    try:
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            # 复制上传的文件内容到临时文件
            shutil.copyfileobj(file.file, temp_file)
            temp_file_path = temp_file.name
        
        try:
            # 存储书籍
            book = await book_shelf.store_book(user_id, temp_file_path, file.filename)
            
            # 返回成功信息
            return JSONResponse(
                status_code=status.HTTP_201_CREATED,
                content={
                    "message": "书籍上传成功",
                    "book_id": book.id,
                    "title": book.title,
                    "author": book.author,
                    "file_name": book.file_name
                }
            )
        except Exception as e:
            logger.error(f"存储书籍失败: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"存储书籍失败: {str(e)}"
            )
        finally:
            # 删除临时文件
            os.unlink(temp_file_path)
    except Exception as e:
        logger.error(f"处理上传文件失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"处理上传文件失败: {str(e)}"
        )

@router.get("/")
async def list_books(
    request: Request = None,
    book_shelf: Annotated[BookShelf, Depends(get_book_shelf)] = None,
    user_id: str = Depends(get_current_user),
    page: int = 1,
    page_size: int = 10,
    sort_by: str = "created_at",
    sort_order: str = "desc"
):
    """
    获取书籍列表
    
    Args:
        page: 页码
        page_size: 每页数量
        sort_by: 排序字段
        sort_order: 排序顺序
        user_id: 用户ID
        book_shelf: 书架服务
        
    Returns:
        JSONResponse: 书籍列表
    """
    try:
        # 获取书籍列表
        books = await book_shelf.list_books(user_id, sort_by, sort_order, page, page_size)
        
        # 构造返回数据
        result = {
            "items": [book.to_dict() for book in books.items],
            "total": books.total,
            "page": books.page,
            "page_size": books.page_size,
            "pages": (books.total + books.page_size - 1) // books.page_size
        }
        
        # 返回书籍列表
        return JSONResponse(content=result)
    except Exception as e:
        logger.error(f"获取书籍列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取书籍列表失败: {str(e)}"
        )

@router.get("/{book_id}")
async def get_book(
    book_id: str,
    book_shelf: Annotated[BookShelf, Depends(get_book_shelf)] = None,
    user_id: str = Depends(get_current_user)
):
    """
    获取书籍详情
    
    Args:
        book_id: 书籍ID
        user_id: 用户ID
        book_shelf: 书架服务
        
    Returns:
        JSONResponse: 书籍详情
    """
    try:
        # 获取书籍详情
        book = await book_shelf.view_book(user_id, book_id)
        
        # 返回书籍详情
        return JSONResponse(content=book.to_dict())
    except Exception as e:
        logger.error(f"获取书籍详情失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到书籍: {book_id}"
        )

@router.put("/{book_id}")
async def update_book(
    book_id: str,
    request: Request,
    book_shelf: Annotated[BookShelf, Depends(get_book_shelf)] = None,
    user_id: str = Depends(get_current_user)
):
    """
    更新书籍元数据
    
    Args:
        book_id: 书籍ID
        request: 请求对象
        user_id: 用户ID
        book_shelf: 书架服务
        
    Returns:
        JSONResponse: 更新成功信息
    """
    try:
        # 获取请求体数据
        data = await request.json()
        
        # 提取元数据
        metadata = {}
        for key in ["title", "author", "description", "publisher", "language", "tags"]:
            if key in data:
                metadata[key] = data[key]
        
        # 更新书籍元数据
        book = await book_shelf.update_book_metadata(user_id, book_id, metadata)
        
        # 返回更新成功信息
        return JSONResponse(
            content={
                "message": "书籍元数据更新成功",
                "book": book.to_dict()
            }
        )
    except Exception as e:
        logger.error(f"更新书籍元数据失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到书籍或更新失败: {book_id}"
        )

@router.get("/{book_id}/download")
async def download_book(
    book_id: str,
    book_shelf: Annotated[BookShelf, Depends(get_book_shelf)] = None,
    user_id: str = Depends(get_current_user)
):
    """
    下载书籍
    
    Args:
        book_id: 书籍ID
        user_id: 用户ID
        book_shelf: 书架服务
        
    Returns:
        FileResponse: 书籍文件
    """
    try:
        # 下载书籍
        book, file_path = await book_shelf.download_book(user_id, book_id)
        
        # 返回文件
        return FileResponse(
            path=file_path,
            filename=book.filename(),
            media_type=book.mime_type()
        )
    except Exception as e:
        logger.error(f"下载书籍失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到书籍: {book_id}"
        )

@router.get("/{book_id}/cover")
async def view_book_cover(
    book_id: str,
    book_shelf: Annotated[BookShelf, Depends(get_book_shelf)] = None,
    user_id: str = Depends(get_current_user)
):
    """
    查看书籍封面
    
    Args:
        book_id: 书籍ID
        user_id: 用户ID
        book_shelf: 书架服务
        
    Returns:
        FileResponse: 书籍封面图片
    """
    try:
        # 获取封面
        cover_path = await book_shelf.view_cover(user_id, book_id)
        
        # 返回封面图片
        return FileResponse(
            path=cover_path,
            media_type="image/jpeg"
        )
    except Exception as e:
        logger.error(f"查看书籍封面失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到书籍封面: {book_id}"
        )

@router.delete("/{book_id}")
async def delete_book(
    book_id: str,
    book_shelf: Annotated[BookShelf, Depends(get_book_shelf)] = None,
    user_id: str = Depends(get_current_user)
):
    """
    删除书籍
    
    Args:
        book_id: 书籍ID
        user_id: 用户ID
        book_shelf: 书架服务
        
    Returns:
        JSONResponse: 删除成功信息
    """
    try:
        # 删除书籍
        await book_shelf.delete_book(user_id, book_id)
        
        # 返回删除成功信息
        return JSONResponse(
            content={
                "message": "书籍删除成功",
                "book_id": book_id
            }
        )
    except Exception as e:
        logger.error(f"删除书籍失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到书籍或删除失败: {book_id}"
        ) 