from abc import ABC, abstractmethod
import datetime
from typing import List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc, asc, func
from sqlalchemy.exc import IntegrityError

from app.entity.book import Book, BookModel, BookAlreadyExistsError


class BookRepo(ABC):
    """
    书籍存储库接口，定义对书籍数据的访问操作。
    """
    
    @abstractmethod
    async def store(self, ctx, book: Book) -> None:
        """
        存储书籍
        
        Args:
            ctx: 上下文
            book: 书籍实体
            
        Raises:
            BookAlreadyExistsError: 书籍已存在时抛出
        """
        pass
    
    @abstractmethod
    async def update(self, ctx, book: Book) -> None:
        """
        更新书籍
        
        Args:
            ctx: 上下文
            book: 书籍实体
            
        Raises:
            ValueError: 书籍不存在时抛出
        """
        pass
    
    @abstractmethod
    async def list(
        self, 
        ctx, 
        sort_by: str = "created_at", 
        sort_order: str = "desc", 
        page: int = 1, 
        per_page: int = 25
    ) -> Tuple[List[Book], int]:
        """
        列出书籍，支持分页和排序
        
        Args:
            ctx: 上下文
            sort_by: 排序字段
            sort_order: 排序顺序 ("asc" 或 "desc")
            page: 页码
            per_page: 每页数量
            
        Returns:
            Tuple[List[Book], int]: 书籍列表和总数量
        """
        pass
    
    @abstractmethod
    async def get_by_id(self, ctx, book_id: str) -> Book:
        """
        通过ID获取书籍
        
        Args:
            ctx: 上下文
            book_id: 书籍ID
            
        Returns:
            Book: 书籍实体
            
        Raises:
            ValueError: 书籍不存在时抛出
        """
        pass
    
    @abstractmethod
    async def get_by_file_hash(self, ctx, file_hash: str) -> Book:
        """
        通过文件哈希获取书籍
        
        Args:
            ctx: 上下文
            file_hash: 文件哈希
            
        Returns:
            Book: 书籍实体
            
        Raises:
            ValueError: 书籍不存在时抛出
        """
        pass
    
    @abstractmethod
    async def count(self, ctx) -> int:
        """
        获取书籍总数
        
        Args:
            ctx: 上下文
            
        Returns:
            int: 书籍总数
        """
        pass


class BookDatabaseRepo(BookRepo):
    """PostgreSQL书籍存储库实现"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def store(self, ctx, book: Book) -> None:
        """存储书籍到PostgreSQL数据库"""
        try:
            db_book = BookModel(
                id=book.id,
                title=book.title,
                author=book.author,
                publisher=book.publisher,
                year=book.year,
                created_at=book.created_at,
                updated_at=book.updated_at,
                isbn=book.isbn,
                document_id=book.document_id,
                file_path=book.file_path,
                format=book.format,
                cover_path=book.cover_path,
            )
            
            self.db.add(db_book)
            await self.db.commit()
        except IntegrityError:
            await self.db.rollback()
            raise BookAlreadyExistsError(f"Book with ID {book.id} already exists")
    
    async def update(self, ctx, book: Book) -> None:
        """更新PostgreSQL数据库中的书籍"""
        stmt = select(BookModel).where(BookModel.id == book.id)
        result = await self.db.execute(stmt)
        db_book = result.scalar_one_or_none()
        
        if not db_book:
            raise ValueError(f"Book with ID {book.id} not found")
        
        # 更新字段
        db_book.title = book.title
        db_book.author = book.author
        db_book.publisher = book.publisher
        db_book.year = book.year
        db_book.updated_at = datetime.datetime.now()
        db_book.isbn = book.isbn
        
        await self.db.commit()
    
    async def list(
        self, 
        ctx, 
        sort_by: str = "created_at", 
        sort_order: str = "desc", 
        page: int = 1, 
        per_page: int = 25
    ) -> Tuple[List[Book], int]:
        """列出PostgreSQL数据库中的书籍"""
        # 验证排序参数
        valid_sort_fields = {
            "title", "author", "publisher", "year", 
            "created_at", "updated_at", "isbn"
        }
        
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"
            
        if sort_order not in {"asc", "desc"}:
            sort_order = "desc"
            
        if page <= 0:
            page = 1
            
        if per_page <= 0 or per_page > 100:
            per_page = 25
        
        # 计算分页
        offset = (page - 1) * per_page
        
        # 构建查询
        stmt = select(BookModel)
        
        # 添加排序
        if sort_order == "desc":
            stmt = stmt.order_by(desc(getattr(BookModel, sort_by)))
        else:
            stmt = stmt.order_by(asc(getattr(BookModel, sort_by)))
        
        # 添加分页
        stmt = stmt.offset(offset).limit(per_page)
        
        # 执行查询
        result = await self.db.execute(stmt)
        db_books = result.scalars().all()
        
        # 统计总数
        count_stmt = select(func.count()).select_from(BookModel)
        count_result = await self.db.execute(count_stmt)
        total_count = count_result.scalar_one()
        
        # 转换为实体
        books = [db_book.to_entity() for db_book in db_books]
        
        return books, total_count
    
    async def get_by_id(self, ctx, book_id: str) -> Book:
        """通过ID获取PostgreSQL数据库中的书籍"""
        stmt = select(BookModel).where(BookModel.id == book_id)
        result = await self.db.execute(stmt)
        db_book = result.scalar_one_or_none()
        
        if not db_book:
            raise ValueError(f"Book with ID {book_id} not found")
        
        return db_book.to_entity()
    
    async def get_by_file_hash(self, ctx, file_hash: str) -> Book:
        """通过文件哈希获取PostgreSQL数据库中的书籍"""
        stmt = select(BookModel).where(BookModel.document_id == file_hash)
        result = await self.db.execute(stmt)
        db_book = result.scalar_one_or_none()
        
        if not db_book:
            raise ValueError(f"Book with file hash {file_hash} not found")
        
        return db_book.to_entity()
    
    async def count(self, ctx) -> int:
        """获取PostgreSQL数据库中的书籍总数"""
        stmt = select(func.count()).select_from(BookModel)
        result = await self.db.execute(stmt)
        return result.scalar_one()


class MemoryBookRepo(BookRepo):
    """内存书籍存储库实现"""
    
    def __init__(self):
        self._books = {}  # id -> Book
        self._hash_index = {}  # file_hash -> id
    
    async def store(self, ctx, book: Book) -> None:
        """存储书籍到内存"""
        if book.id in self._books:
            raise BookAlreadyExistsError(f"Book with ID {book.id} already exists")
        
        self._books[book.id] = book
        if book.document_id:
            self._hash_index[book.document_id] = book.id
    
    async def update(self, ctx, book: Book) -> None:
        """更新内存中的书籍"""
        if book.id not in self._books:
            raise ValueError(f"Book with ID {book.id} not found")
        
        old_book = self._books[book.id]
        
        # 创建更新后的书籍对象
        updated_book = Book(
            id=old_book.id,
            title=book.title if book.title else old_book.title,
            author=book.author if book.author else old_book.author,
            publisher=book.publisher if book.publisher else old_book.publisher,
            year=book.year if book.year else old_book.year,
            created_at=old_book.created_at,
            updated_at=datetime.datetime.now(),
            isbn=book.isbn if book.isbn else old_book.isbn,
            document_id=old_book.document_id,
            file_path=old_book.file_path,
            format=old_book.format,
            cover_path=old_book.cover_path,
        )
        
        self._books[book.id] = updated_book
    
    async def list(
        self, 
        ctx, 
        sort_by: str = "created_at", 
        sort_order: str = "desc", 
        page: int = 1, 
        per_page: int = 25
    ) -> Tuple[List[Book], int]:
        """列出内存中的书籍"""
        # 验证排序参数
        valid_sort_fields = {
            "title", "author", "publisher", "year", 
            "created_at", "updated_at", "isbn"
        }
        
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"
            
        if sort_order not in {"asc", "desc"}:
            sort_order = "desc"
            
        if page <= 0:
            page = 1
            
        if per_page <= 0 or per_page > 100:
            per_page = 25
        
        # 获取所有书籍并排序
        books = list(self._books.values())
        
        # 排序
        reverse = sort_order == "desc"
        books.sort(key=lambda book: getattr(book, sort_by), reverse=reverse)
        
        # 分页
        total_count = len(books)
        start_idx = (page - 1) * per_page
        end_idx = start_idx + per_page
        
        return books[start_idx:end_idx], total_count
    
    async def get_by_id(self, ctx, book_id: str) -> Book:
        """通过ID获取内存中的书籍"""
        if book_id not in self._books:
            raise ValueError(f"Book with ID {book_id} not found")
        
        return self._books[book_id]
    
    async def get_by_file_hash(self, ctx, file_hash: str) -> Book:
        """通过文件哈希获取内存中的书籍"""
        if file_hash not in self._hash_index:
            raise ValueError(f"Book with file hash {file_hash} not found")
        
        book_id = self._hash_index[file_hash]
        return self._books[book_id]
    
    async def count(self, ctx) -> int:
        """获取内存中的书籍总数"""
        return len(self._books) 