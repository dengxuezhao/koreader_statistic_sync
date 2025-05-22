import logging
import time
from typing import Optional, List

from app.entity.progress import Progress
from app.repository.progress_repo import ProgressRepo


class ProgressSync:
    """
    进度同步服务，处理KOReader的阅读进度同步。
    """
    
    def __init__(self, progress_repo: ProgressRepo):
        """
        初始化进度同步服务
        
        Args:
            progress_repo: 进度存储库
        """
        self.progress_repo = progress_repo
        self.logger = logging.getLogger(__name__)
    
    async def sync(self, ctx, progress_data: Progress) -> Progress:
        """
        同步阅读进度
        
        Args:
            ctx: 上下文
            progress_data: 进度数据
            
        Returns:
            Progress: 同步后的进度数据
        """
        self.logger.info(f"同步进度: {progress_data.document}")
        
        # 获取最新的进度记录
        history = await self.progress_repo.get_book_history(ctx, progress_data.document, 1)
        
        # 检查是否有更新的进度
        if history and history[0].timestamp > progress_data.timestamp:
            self.logger.info(f"服务器有更新的进度: {history[0].timestamp} > {progress_data.timestamp}")
            return history[0]
        
        # 存储新的进度
        await self.progress_repo.store(ctx, progress_data)
        
        # 确保有一个非空的时间戳
        if not progress_data.timestamp:
            progress_data.timestamp = int(time.time())
        
        return progress_data
    
    async def fetch(self, ctx, document_id: str) -> Optional[Progress]:
        """
        获取阅读进度
        
        Args:
            ctx: 上下文
            document_id: 文档ID
            
        Returns:
            Optional[Progress]: 进度数据，如果不存在则返回None
        """
        self.logger.info(f"获取进度: {document_id}")
        
        # 获取最新的进度记录
        history = await self.progress_repo.get_book_history(ctx, document_id, 1)
        
        if not history:
            self.logger.info(f"未找到进度: {document_id}")
            return None
        
        return history[0]
    
    async def get_history(self, ctx, document_id: str, limit: int = 10) -> List[Progress]:
        """
        获取阅读历史
        
        Args:
            ctx: 上下文
            document_id: 文档ID
            limit: 返回的历史记录数量
            
        Returns:
            List[Progress]: 进度历史列表
        """
        self.logger.info(f"获取历史: {document_id}, limit={limit}")
        
        return await self.progress_repo.get_book_history(ctx, document_id, limit) 