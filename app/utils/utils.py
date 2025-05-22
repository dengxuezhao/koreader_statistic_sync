import os
import hashlib
import logging
from typing import TypeVar, Generic, Any

logger = logging.getLogger(__name__)

# 类型变量，用于泛型函数
T = TypeVar('T')


def partial_md5(file_path: str, chunk_size: int = 5*1024*1024) -> str:
    """
    计算文件的部分MD5哈希值，与KOReader兼容
    KOReader使用文件的前5MB计算MD5
    
    Args:
        file_path: 文件路径
        chunk_size: 计算哈希的块大小（字节）
        
    Returns:
        str: MD5哈希值（16进制字符串）
    """
    try:
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            data = f.read(chunk_size)
            md5.update(data)
        return md5.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating partial MD5 for {file_path}: {str(e)}")
        return ""


def full_md5(file_path: str) -> str:
    """
    计算文件的完整MD5哈希值
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: MD5哈希值（16进制字符串）
    """
    try:
        md5 = hashlib.md5()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                md5.update(chunk)
        return md5.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating full MD5 for {file_path}: {str(e)}")
        return ""


def ensure_dir(dir_path: str) -> bool:
    """
    确保目录存在，如果不存在则创建
    
    Args:
        dir_path: 目录路径
        
    Returns:
        bool: 如果目录存在或成功创建则返回True，否则返回False
    """
    try:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        return True
    except Exception as e:
        logger.error(f"Error creating directory {dir_path}: {str(e)}")
        return False


def safe_filename(filename: str) -> str:
    """
    创建安全的文件名，移除或替换不安全字符
    
    Args:
        filename: 原始文件名
        
    Returns:
        str: 安全的文件名
    """
    # 替换常见的不安全字符
    unsafe_chars = ['/', '\\', ':', '*', '?', '"', '<', '>', '|']
    safe_name = filename
    for char in unsafe_chars:
        safe_name = safe_name.replace(char, '_')
    return safe_name


def if_null(value: T, default: T) -> T:
    """
    如果值为None，则返回默认值
    
    Args:
        value: 要检查的值
        default: 默认值
        
    Returns:
        如果value不为None，则返回value，否则返回default
    """
    return value if value is not None else default


def get_file_extension(file_path: str) -> str:
    """
    获取文件扩展名（不包含点）
    
    Args:
        file_path: 文件路径
        
    Returns:
        str: 文件扩展名（小写）
    """
    return os.path.splitext(file_path)[1].lower().lstrip('.')


def format_file_size(size_bytes: int) -> str:
    """
    格式化文件大小，转换为人类可读格式
    
    Args:
        size_bytes: 文件大小（字节）
        
    Returns:
        str: 格式化后的文件大小
    """
    # 定义单位
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(size_bytes)
    unit_index = 0
    
    # 转换单位
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    # 格式化输出
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}" 