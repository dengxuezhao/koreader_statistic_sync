import os
import aiofiles
from typing import Optional
from sqlalchemy import Column, String, LargeBinary, DateTime, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.database import Base
from app.storage.base import Storage, create_temp_file


class FileModel(Base):
    """存储在PostgreSQL中的文件的SQLAlchemy ORM模型"""
    __tablename__ = "files"
    
    filepath = Column(String, primary_key=True)
    content = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())


class PostgresStorage(Storage):
    """
    PostgreSQL存储实现，将文件内容存储在PostgreSQL数据库中。
    """
    
    def __init__(self, db: AsyncSession):
        """
        初始化PostgreSQL存储。
        
        Args:
            db: SQLAlchemy异步会话
        """
        self.db = db
    
    async def write(self, source_path: str, destination_path: str) -> None:
        """
        将文件从源路径写入到PostgreSQL存储中。
        
        Args:
            source_path: 源文件路径
            destination_path: 目标存储路径
            
        Raises:
            IOError: 写入失败时抛出
        """
        try:
            async with aiofiles.open(source_path, 'rb') as f:
                content = await f.read()
            
            file_obj = FileModel(
                filepath=destination_path,
                content=content
            )
            
            # 检查文件是否已存在
            stmt = select(FileModel).where(FileModel.filepath == destination_path)
            result = await self.db.execute(stmt)
            existing_file = result.scalar_one_or_none()
            
            if existing_file:
                existing_file.content = content
            else:
                self.db.add(file_obj)
            
            await self.db.commit()
            
        except Exception as e:
            await self.db.rollback()
            raise IOError(f"Failed to write file to PostgreSQL: {str(e)}") from e
    
    async def read(self, filepath: str) -> Optional[os.PathLike]:
        """
        从PostgreSQL存储中读取文件并返回临时文件路径。
        
        Args:
            filepath: 存储中的文件路径
            
        Returns:
            临时文件路径，如果文件不存在则返回None
            
        Raises:
            FileNotFoundError: 文件不存在时抛出
            IOError: 读取失败时抛出
        """
        stmt = select(FileModel).where(FileModel.filepath == filepath)
        result = await self.db.execute(stmt)
        file_obj = result.scalar_one_or_none()
        
        if not file_obj:
            raise FileNotFoundError(f"File not found in PostgreSQL: {filepath}")
        
        try:
            return await create_temp_file(file_obj.content)
        except Exception as e:
            raise IOError(f"Failed to read file from PostgreSQL: {str(e)}") from e 