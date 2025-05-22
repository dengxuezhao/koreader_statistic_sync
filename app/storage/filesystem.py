import os
import shutil
import aiofiles
from typing import Optional
from pathlib import Path

from app.storage.base import Storage


class FilesystemStorage(Storage):
    """
    文件系统存储实现，将文件存储在本地文件系统中。
    """
    
    def __init__(self, base_dir: str):
        """
        初始化文件系统存储。
        
        Args:
            base_dir: 基础目录路径，所有文件都将相对于此目录存储
        """
        self.base_dir = Path(base_dir)
        # 确保基础目录存在
        os.makedirs(self.base_dir, exist_ok=True)
    
    async def write(self, source_path: str, destination_path: str) -> None:
        """
        将文件从源路径写入到文件系统存储中。
        
        Args:
            source_path: 源文件路径
            destination_path: 目标存储路径（相对于基础目录）
            
        Raises:
            IOError: 写入失败时抛出
        """
        try:
            # 解析目标文件的完整路径
            full_dest_path = self.base_dir / destination_path
            
            # 确保目标目录存在
            os.makedirs(os.path.dirname(full_dest_path), exist_ok=True)
            
            # 复制文件
            shutil.copy2(source_path, full_dest_path)
        except Exception as e:
            raise IOError(f"Failed to write file to filesystem: {str(e)}") from e
    
    async def read(self, filepath: str) -> Optional[os.PathLike]:
        """
        从文件系统存储中读取文件。
        由于文件已经在文件系统中，直接返回完整路径。
        
        Args:
            filepath: 存储中的文件路径（相对于基础目录）
            
        Returns:
            文件的完整路径，如果文件不存在则抛出异常
            
        Raises:
            FileNotFoundError: 文件不存在时抛出
        """
        full_path = self.base_dir / filepath
        
        if not os.path.exists(full_path):
            raise FileNotFoundError(f"File not found in filesystem: {filepath}")
        
        return full_path 