import os
import tempfile
from abc import ABC, abstractmethod
from typing import Optional, BinaryIO


class Storage(ABC):
    """
    存储抽象基类，定义文件存储接口。
    具体实现可以包括PostgreSQL、文件系统或内存存储。
    """
    
    @abstractmethod
    async def write(self, source_path: str, destination_path: str) -> None:
        """
        将文件从源路径写入到存储中。
        
        Args:
            source_path: 源文件路径
            destination_path: 目标存储路径
            
        Raises:
            IOError: 写入失败时抛出
        """
        pass
    
    @abstractmethod
    async def read(self, filepath: str) -> Optional[os.PathLike]:
        """
        从存储中读取文件并返回临时文件路径。
        
        Args:
            filepath: 存储中的文件路径
            
        Returns:
            临时文件对象，如果文件不存在则返回None
            
        Raises:
            FileNotFoundError: 文件不存在时抛出
            IOError: 读取失败时抛出
        """
        pass


async def create_temp_file(content: bytes) -> str:
    """
    创建一个包含指定内容的临时文件。
    
    Args:
        content: 要写入临时文件的字节内容
        
    Returns:
        临时文件路径
    """
    fd, path = tempfile.mkstemp()
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(content)
        return path
    except:
        os.unlink(path)
        raise 