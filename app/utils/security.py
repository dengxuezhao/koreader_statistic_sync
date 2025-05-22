import hashlib
import os
import base64
from datetime import datetime, timedelta
from typing import Union, Any, Optional
from passlib.context import CryptContext
from jose import jwt, JWTError

from app.config import get_settings

# 密码哈希上下文
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# 配置
settings = get_settings()


def get_password_hash(password: str) -> str:
    """
    使用bcrypt对密码进行哈希处理
    
    Args:
        password: 明文密码
        
    Returns:
        str: 哈希后的密码
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    验证明文密码与哈希密码是否匹配
    
    Args:
        plain_password: 明文密码
        hashed_password: 哈希后的密码
        
    Returns:
        bool: 密码是否匹配
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_md5_hash(text: str) -> str:
    """
    获取字符串的MD5哈希值
    
    Args:
        text: 要哈希的字符串
        
    Returns:
        str: MD5哈希值
    """
    m = hashlib.md5()
    m.update(text.encode('utf-8'))
    return m.hexdigest()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    创建JWT访问令牌
    
    Args:
        data: 要编码到令牌中的数据
        expires_delta: 令牌过期时间
        
    Returns:
        str: JWT令牌
    """
    to_encode = data.copy()
    
    # 设置过期时间
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    
    # 添加过期时间声明
    to_encode.update({"exp": expire})
    
    # 编码JWT
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    return encoded_jwt


def decode_access_token(token: str) -> Union[dict, None]:
    """
    解码JWT访问令牌
    
    Args:
        token: JWT令牌
        
    Returns:
        Union[dict, None]: 解码后的数据或None（如果令牌无效）
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def generate_random_token(length: int = 32) -> str:
    """
    生成随机令牌
    
    Args:
        length: 令牌长度（字节）
        
    Returns:
        str: Base64编码的随机令牌
    """
    return base64.urlsafe_b64encode(os.urandom(length)).decode('utf-8') 