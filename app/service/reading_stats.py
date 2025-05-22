import logging
import os
import tempfile
import sqlite3
from typing import Optional, Dict, Any, List, IO
import aiofiles
import json
from datetime import datetime

from app.storage import Storage


class ReadingStats:
    """
    阅读统计服务，处理KOReader的阅读统计数据。
    
    KOReader使用SQLite数据库存储阅读统计数据，该服务负责处理这些数据。
    """
    
    def __init__(self, storage: Storage):
        """
        初始化阅读统计服务
        
        Args:
            storage: 存储接口，用于保存统计数据文件
        """
        self.storage = storage
        self.logger = logging.getLogger(__name__)
    
    async def write(self, ctx, data: IO, device_name: str) -> None:
        """
        写入阅读统计数据
        
        Args:
            ctx: 上下文
            data: 统计数据（SQLite数据库）
            device_name: 设备名称
            
        Raises:
            IOError: 写入失败时抛出
        """
        self.logger.info(f"写入统计数据: 设备={device_name}")
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite3") as temp_file:
            # 保存上传的数据到临时文件
            temp_file.write(data.read())
            temp_path = temp_file.name
        
        try:
            # 构建存储路径
            storage_path = f"stats/{device_name}/statistics.sqlite3"
            
            # 存储文件
            await self.storage.write(temp_path, storage_path)
            
            # 提取并存储统计摘要
            summary = self._extract_stats_summary(temp_path)
            if summary:
                # 将摘要转换为JSON
                json_summary = json.dumps(summary)
                
                # 创建摘要临时文件
                with tempfile.NamedTemporaryFile(delete=False, suffix=".json") as summary_file:
                    summary_file.write(json_summary.encode('utf-8'))
                    summary_path = summary_file.name
                
                # 存储摘要文件
                summary_storage_path = f"stats/{device_name}/summary.json"
                await self.storage.write(summary_path, summary_storage_path)
                
                # 删除临时文件
                os.unlink(summary_path)
        finally:
            # 删除临时文件
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    
    async def read(self, ctx, device_name: str) -> Optional[str]:
        """
        读取阅读统计数据
        
        Args:
            ctx: 上下文
            device_name: 设备名称
            
        Returns:
            Optional[str]: 统计数据文件路径，如果不存在则返回None
            
        Raises:
            FileNotFoundError: 文件不存在时抛出
        """
        self.logger.info(f"读取统计数据: 设备={device_name}")
        
        try:
            # 构建存储路径
            storage_path = f"stats/{device_name}/statistics.sqlite3"
            
            # 读取文件
            return await self.storage.read(storage_path)
        except FileNotFoundError:
            self.logger.warning(f"未找到统计数据: 设备={device_name}")
            return None
    
    async def get_summary(self, ctx, device_name: str) -> Dict[str, Any]:
        """
        获取统计摘要
        
        Args:
            ctx: 上下文
            device_name: 设备名称
            
        Returns:
            Dict[str, Any]: 统计摘要，如果不存在则返回空字典
        """
        self.logger.info(f"获取统计摘要: 设备={device_name}")
        
        try:
            # 构建存储路径
            storage_path = f"stats/{device_name}/summary.json"
            
            # 读取文件
            temp_path = await self.storage.read(storage_path)
            
            # 读取JSON数据
            async with aiofiles.open(temp_path, 'r') as f:
                data = await f.read()
                return json.loads(data)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            self.logger.warning(f"获取统计摘要失败: {str(e)}")
            return {}
    
    async def list_devices(self, ctx) -> List[str]:
        """
        列出有统计数据的设备
        
        Args:
            ctx: 上下文
            
        Returns:
            List[str]: 设备名称列表
            
        注意：此方法需要存储接口支持列出目录，目前的实现不支持
        """
        # 此功能需要存储接口支持列出目录
        # 暂时返回空列表，后续可以实现此功能
        return []
    
    def _extract_stats_summary(self, db_path: str) -> Dict[str, Any]:
        """
        从SQLite数据库中提取统计摘要
        
        Args:
            db_path: 数据库文件路径
            
        Returns:
            Dict[str, Any]: 统计摘要
        """
        summary = {
            "total_books": 0,
            "total_pages": 0,
            "total_time": 0,  # 阅读时间（秒）
            "last_updated": datetime.now().isoformat(),
            "books": []
        }
        
        try:
            # 连接数据库
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # 获取总统计数据
            cursor.execute("SELECT COUNT(*) as total_books, SUM(pages) as total_pages, SUM(duration) as total_time FROM book")
            row = cursor.fetchone()
            if row:
                summary["total_books"] = row["total_books"] or 0
                summary["total_pages"] = row["total_pages"] or 0
                summary["total_time"] = row["total_time"] or 0
            
            # 获取最近阅读的书籍
            cursor.execute("""
                SELECT title, authors, pages, duration, last_open
                FROM book
                ORDER BY last_open DESC
                LIMIT 10
            """)
            
            for row in cursor.fetchall():
                book = {
                    "title": row["title"],
                    "authors": row["authors"],
                    "pages": row["pages"],
                    "duration": row["duration"],  # 阅读时间（秒）
                    "last_open": row["last_open"]
                }
                summary["books"].append(book)
            
            conn.close()
            return summary
        except sqlite3.Error as e:
            self.logger.error(f"提取统计摘要失败: {str(e)}")
            return summary 