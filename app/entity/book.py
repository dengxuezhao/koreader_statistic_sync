import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, DateTime, func
from pydantic import BaseModel, Field

from app.database import Base


# 自定义异常
class BookAlreadyExistsError(Exception):
    """当尝试添加已存在的书籍时抛出"""
    pass


class Book:
    """
    书籍实体，表示系统中的一本书。
    这是一个领域模型类，独立于ORM或数据库实现。
    """
    def __init__(
        self,
        id: str,
        title: str,
        author: str = "",
        publisher: str = "",
        year: int = 0,
        created_at: Optional[datetime.datetime] = None,
        updated_at: Optional[datetime.datetime] = None,
        isbn: str = "",
        document_id: str = "",
        file_path: str = "",
        format: str = "",
        cover_path: str = "",
    ):
        self.id = id
        self.title = title
        self.author = author
        self.publisher = publisher
        self.year = year
        self.created_at = created_at or datetime.datetime.now()
        self.updated_at = updated_at or self.created_at
        self.isbn = isbn
        self.document_id = document_id  # md5 hash for file content
        self.file_path = file_path
        self.format = format
        self.cover_path = cover_path
    
    def extension(self) -> str:
        """获取文件扩展名"""
        if not self.file_path:
            return ""
        return self.file_path.split(".")[-1]
    
    def filename(self) -> str:
        """生成下载文件名"""
        basename = f"{self.id}.{self.extension()}"
        if not self.author:
            return f"{self.title} -- {basename}"
        return f"{self.title} - {self.author} -- {basename}"
    
    def mime_type(self) -> str:
        """根据文件扩展名确定MIME类型"""
        ext = self.extension()
        mime_types = {
            "epub": "application/epub+zip",
            "pdf": "application/pdf",
            "mobi": "application/x-mobipocket-ebook",
            "fb2": "application/fb2",
        }
        return mime_types.get(ext, "")


# SQLAlchemy ORM模型
class BookModel(Base):
    """书籍的SQLAlchemy ORM模型"""
    __tablename__ = "books"
    
    id = Column(String, primary_key=True)
    title = Column(String, nullable=False)
    author = Column(String)
    publisher = Column(String)
    year = Column(Integer)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    isbn = Column(String)
    document_id = Column(String, index=True)
    file_path = Column(String)
    format = Column(String)
    cover_path = Column(String)
    
    def to_entity(self) -> Book:
        """将ORM模型转换为领域实体"""
        return Book(
            id=self.id,
            title=self.title,
            author=self.author,
            publisher=self.publisher,
            year=self.year,
            created_at=self.created_at,
            updated_at=self.updated_at,
            isbn=self.isbn,
            document_id=self.document_id,
            file_path=self.file_path,
            format=self.format,
            cover_path=self.cover_path,
        )


# Pydantic模型，用于API请求和响应
class BookCreate(BaseModel):
    """用于创建新书籍的Pydantic模型"""
    title: str
    author: Optional[str] = ""
    publisher: Optional[str] = ""
    year: Optional[int] = 0
    isbn: Optional[str] = ""


class BookUpdate(BaseModel):
    """用于更新书籍的Pydantic模型"""
    title: Optional[str] = None
    author: Optional[str] = None
    publisher: Optional[str] = None
    year: Optional[int] = None
    isbn: Optional[str] = None


class BookResponse(BaseModel):
    """用于API响应的书籍Pydantic模型"""
    id: str
    title: str
    author: str
    publisher: str
    year: int
    created_at: datetime.datetime
    updated_at: datetime.datetime
    isbn: str
    document_id: str
    format: str
    
    class Config:
        orm_mode = True 