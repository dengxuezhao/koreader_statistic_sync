from abc import ABC, abstractmethod
import datetime
import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import desc

from app.entity.progress import Progress, ProgressModel


class ProgressRepo(ABC):
    """
    进度存储库接口，定义对阅读进度数据的访问操作。
    """
    
    @abstractmethod
    async def store(self, ctx, progress: Progress) -> None:
        """
        存储阅读进度
        
        Args:
            ctx: 上下文
            progress: 阅读进度实体
        """
        pass
    
    @abstractmethod
    async def get_book_history(self, ctx, book_id: str, limit: int = 10) -> List[Progress]:
        """
        获取书籍的阅读历史
        
        Args:
            ctx: 上下文
            book_id: 书籍ID（文档哈希）
            limit: 返回的历史记录数量
            
        Returns:
            List[Progress]: 阅读进度历史列表
        """
        pass


class ProgressDatabaseRepo(ProgressRepo):
    """PostgreSQL进度存储库实现"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def store(self, ctx, progress: Progress) -> None:
        """存储阅读进度到PostgreSQL数据库"""
        # 生成唯一ID
        progress_id = str(uuid.uuid4())
        
        # 创建ORM模型
        db_progress = ProgressModel(
            id=progress_id,
            document=progress.document,
            percentage=progress.percentage,
            progress=progress.progress,
            device=progress.device,
            device_id=progress.device_id,
            timestamp=progress.timestamp,
            auth_device_name=progress.auth_device_name
        )
        
        # 保存到数据库
        self.db.add(db_progress)
        await self.db.commit()
    
    async def get_book_history(self, ctx, book_id: str, limit: int = 10) -> List[Progress]:
        """获取PostgreSQL数据库中书籍的阅读历史"""
        # 构建查询
        stmt = (
            select(ProgressModel)
            .where(ProgressModel.document == book_id)
            .order_by(desc(ProgressModel.timestamp))
            .limit(limit)
        )
        
        # 执行查询
        result = await self.db.execute(stmt)
        db_progress_list = result.scalars().all()
        
        # 转换为实体
        progress_list = [db_progress.to_entity() for db_progress in db_progress_list]
        
        return progress_list


class MemoryProgressRepo(ProgressRepo):
    """内存进度存储库实现"""
    
    def __init__(self):
        # 使用字典存储进度，键是(document, timestamp)元组
        self._progress = {}
        # 文档索引，键是document，值是按timestamp排序的进度列表
        self._document_index = {}
    
    async def store(self, ctx, progress: Progress) -> None:
        """存储阅读进度到内存"""
        # 创建键
        key = (progress.document, progress.timestamp)
        
        # 存储进度
        self._progress[key] = progress
        
        # 更新文档索引
        if progress.document not in self._document_index:
            self._document_index[progress.document] = []
        self._document_index[progress.document].append(progress)
        
        # 按时间戳排序
        self._document_index[progress.document].sort(
            key=lambda p: p.timestamp, 
            reverse=True
        )
    
    async def get_book_history(self, ctx, book_id: str, limit: int = 10) -> List[Progress]:
        """获取内存中书籍的阅读历史"""
        if book_id not in self._document_index:
            return []
        
        # 获取并限制结果数量
        return self._document_index[book_id][:limit] 