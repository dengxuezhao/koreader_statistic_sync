import os
import aiofiles
from typing import Dict, Optional
from pathlib import Path

from app.storage.base import Storage, create_temp_file


class MemoryStorage(Storage):
    """
    内存存储实现，将文件存储在内存中。
    主要用于测试目的，不应用于生产环境。
    """
    
    def __init__(self):
        """初始化内存存储。"""
        # 使用字典存储文件内容，键是文件路径，值是文件内容
        self._files: Dict[str, bytes] = {}
    
    async def write(self, source_path: str, destination_path: str) -> None:
        """
        将文件从源路径写入到内存存储中。
        
        Args:
            source_path: 源文件路径
            destination_path: 目标存储路径
            
        Raises:
            IOError: 写入失败时抛出
        """
        try:
            async with aiofiles.open(source_path, 'rb') as f:
                content = await f.read()
            
            self._files[destination_path] = content
        except Exception as e:
            raise IOError(f"Failed to write file to memory: {str(e)}") from e
    
    async def read(self, filepath: str) -> Optional[os.PathLike]:
        """
        从内存存储中读取文件并返回临时文件路径。
        
        Args:
            filepath: 存储中的文件路径
            
        Returns:
            临时文件路径，如果文件不存在则抛出异常
            
        Raises:
            FileNotFoundError: 文件不存在时抛出
            IOError: 创建临时文件失败时抛出
        """
        if filepath not in self._files:
            raise FileNotFoundError(f"File not found in memory: {filepath}")
        
        try:
            return await create_temp_file(self._files[filepath])
        except Exception as e:
            raise IOError(f"Failed to create temporary file: {str(e)}") from e
    
    def clear(self) -> None:
        """清除所有存储的文件。"""
        self._files.clear()
    
    def get_file_content(self, filepath: str) -> Optional[bytes]:
        """
        获取文件内容。
        用于测试目的。
        
        Args:
            filepath: 文件路径
            
        Returns:
            文件内容，如果文件不存在则返回None
        """
        return self._files.get(filepath) 