import os
import tempfile
import logging
import datetime
import uuid
from typing import Tuple, Optional, List

from app.entity.book import Book, BookAlreadyExistsError
from app.repository.book_repo import BookRepo
from app.storage.base import Storage
from app.utils.paginator import PaginatedBookList
from app.utils.metadata import extract_book_metadata, resize_cover
from app.utils.utils import partial_md5, safe_filename, ensure_dir


class BookShelf:
    """
    书架服务，处理书籍的存储、检索和元数据管理。
    """
    
    def __init__(self, storage: Storage, repo: BookRepo, logger: logging.Logger):
        """
        初始化书架服务
        
        Args:
            storage: 存储接口
            repo: 书籍存储库
            logger: 日志记录器
        """
        self.storage = storage
        self.repo = repo
        self.logger = logger
    
    async def store_book(self, ctx, temp_file: str, uploaded_filename: str) -> Book:
        """
        存储书籍
        
        Args:
            ctx: 上下文
            temp_file: 临时文件路径
            uploaded_filename: 上传的文件名
            
        Returns:
            Book: 存储的书籍
            
        Raises:
            BookAlreadyExistsError: 书籍已存在时抛出
            ValueError: 未知文件格式或其他错误
        """
        # 计算KOReader部分MD5哈希
        file_hash = partial_md5(temp_file)
        if not file_hash:
            raise ValueError("Failed to calculate file hash")
        
        # 检查是否已存在
        try:
            existing_book = await self.repo.get_by_file_hash(ctx, file_hash)
            self.logger.info(f"Book with hash {file_hash} already exists")
            raise BookAlreadyExistsError(f"Book with hash {file_hash} already exists")
        except ValueError:
            # 书籍不存在，继续处理
            pass
        
        # 提取元数据
        metadata = extract_book_metadata(temp_file)
        if not metadata.format:
            raise ValueError("Unknown file format")
        
        # 生成唯一ID和创建日期
        book_id = str(uuid.uuid4())
        create_date = datetime.datetime.now()
        
        # 构建存储路径
        year_month_day = create_date.strftime("%Y/%m/%d")
        storage_path = f"{year_month_day}/{book_id}.{metadata.format}"
        
        # 存储文件
        try:
            await self.storage.write(temp_file, storage_path)
        except Exception as e:
            self.logger.error(f"Failed to store book: {str(e)}")
            raise ValueError(f"Failed to store book: {str(e)}")
        
        # 处理封面
        cover_path = ""
        if metadata.cover:
            try:
                # 调整封面大小
                resized_cover = resize_cover(metadata.cover)
                
                # 创建临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as cover_file:
                    cover_file.write(resized_cover)
                    cover_temp_path = cover_file.name
                
                # 存储封面
                cover_path = f"covers/{book_id}.jpg"
                await self.storage.write(cover_temp_path, cover_path)
                
                # 删除临时文件
                os.unlink(cover_temp_path)
            except Exception as e:
                self.logger.error(f"Failed to process cover: {str(e)}")
                # 继续处理，即使封面处理失败
        
        # 创建书籍对象
        book = Book(
            id=book_id,
            title=metadata.title,
            author=metadata.author,
            publisher=metadata.publisher,
            year=0,  # 暂时没有年份数据
            created_at=create_date,
            updated_at=create_date,
            isbn=metadata.isbn,
            document_id=file_hash,
            file_path=storage_path,
            format=metadata.format,
            cover_path=cover_path,
        )
        
        # 存储书籍元数据
        await self.repo.store(ctx, book)
        
        return book
    
    async def list_books(
        self, 
        ctx, 
        sort_by: str = "created_at", 
        sort_order: str = "desc", 
        page: int = 1, 
        per_page: int = 25
    ) -> PaginatedBookList:
        """
        列出书籍
        
        Args:
            ctx: 上下文
            sort_by: 排序字段
            sort_order: 排序顺序 ("asc" 或 "desc")
            page: 页码
            per_page: 每页数量
            
        Returns:
            PaginatedBookList: 分页的书籍列表
        """
        books, total_count = await self.repo.list(ctx, sort_by, sort_order, page, per_page)
        
        return PaginatedBookList(
            items=books,
            per_page=per_page,
            current_page=page,
            total_count=total_count
        )
    
    async def view_book(self, ctx, book_id: str) -> Book:
        """
        查看书籍详情
        
        Args:
            ctx: 上下文
            book_id: 书籍ID
            
        Returns:
            Book: 书籍详情
            
        Raises:
            ValueError: 书籍不存在时抛出
        """
        return await self.repo.get_by_id(ctx, book_id)
    
    async def update_book_metadata(self, ctx, book_id: str, metadata: Book) -> Book:
        """
        更新书籍元数据
        
        Args:
            ctx: 上下文
            book_id: 书籍ID
            metadata: 包含要更新字段的书籍对象
            
        Returns:
            Book: 更新后的书籍
            
        Raises:
            ValueError: 书籍不存在时抛出
        """
        # 获取现有书籍
        book = await self.repo.get_by_id(ctx, book_id)
        
        # 创建更新后的书籍对象
        updated_book = Book(
            id=book.id,
            title=metadata.title if metadata.title else book.title,
            author=metadata.author if metadata.author else book.author,
            publisher=metadata.publisher if metadata.publisher else book.publisher,
            year=metadata.year if metadata.year else book.year,
            created_at=book.created_at,
            updated_at=datetime.datetime.now(),
            isbn=metadata.isbn if metadata.isbn else book.isbn,
            document_id=book.document_id,
            file_path=book.file_path,
            format=book.format,
            cover_path=book.cover_path,
        )
        
        # 更新书籍
        await self.repo.update(ctx, updated_book)
        
        return updated_book
    
    async def download_book(self, ctx, book_id: str) -> Tuple[Book, str]:
        """
        下载书籍
        
        Args:
            ctx: 上下文
            book_id: 书籍ID
            
        Returns:
            Tuple[Book, str]: 书籍对象和临时文件路径
            
        Raises:
            ValueError: 书籍不存在或读取失败时抛出
        """
        # 获取书籍
        book = await self.repo.get_by_id(ctx, book_id)
        
        # 读取文件
        try:
            file_path = await self.storage.read(book.file_path)
            return book, file_path
        except Exception as e:
            self.logger.error(f"Failed to read book file: {str(e)}")
            raise ValueError(f"Failed to read book file: {str(e)}")
    
    async def view_cover(self, ctx, book_id: str) -> str:
        """
        查看书籍封面
        
        Args:
            ctx: 上下文
            book_id: 书籍ID
            
        Returns:
            str: 封面文件的临时路径
            
        Raises:
            ValueError: 书籍不存在、没有封面或读取失败时抛出
        """
        # 获取书籍
        book = await self.repo.get_by_id(ctx, book_id)
        
        # 检查是否有封面
        if not book.cover_path:
            raise ValueError(f"Book {book_id} has no cover")
        
        # 读取封面
        try:
            cover_path = await self.storage.read(book.cover_path)
            return cover_path
        except Exception as e:
            self.logger.error(f"Failed to read cover file: {str(e)}")
            raise ValueError(f"Failed to read cover file: {str(e)}") 