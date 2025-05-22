import datetime
import ipaddress
from typing import Optional, List
from sqlalchemy import Column, String, DateTime, func, ForeignKey
from sqlalchemy.orm import relationship
from pydantic import BaseModel, Field

from app.database import Base


# 自定义异常
class UserAlreadyExistsError(Exception):
    """当尝试创建已存在的用户时抛出"""
    pass


class UserNotFoundError(Exception):
    """当用户不存在时抛出"""
    pass


class SessionNotFoundError(Exception):
    """当会话不存在时抛出"""
    pass


class DeviceAlreadyExistsError(Exception):
    """当尝试创建已存在的设备时抛出"""
    pass


class DeviceNotFoundError(Exception):
    """当设备不存在时抛出"""
    pass


class IncorrectPasswordError(Exception):
    """当密码不正确时抛出"""
    pass


class User:
    """
    用户实体，表示系统的用户账户。
    这是一个领域模型类，独立于ORM或数据库实现。
    """
    def __init__(self, username: str, hashed_password: str):
        self.username = username
        self.hashed_password = hashed_password


class Device:
    """
    设备实体，表示KOReader设备。
    这是一个领域模型类，独立于ORM或数据库实现。
    """
    def __init__(self, name: str, hashed_password: str):
        self.name = name
        self.hashed_password = hashed_password


class Session:
    """
    会话实体，表示用户认证会话。
    这是一个领域模型类，独立于ORM或数据库实现。
    """
    def __init__(
        self,
        session_key: str,
        username: str,
        user_agent: str,
        client_ip: ipaddress.IPv4Address,
        created_at: Optional[datetime.datetime] = None,
    ):
        self.session_key = session_key
        self.username = username
        self.user_agent = user_agent
        self.client_ip = client_ip
        self.created_at = created_at or datetime.datetime.now()


# SQLAlchemy ORM模型
class UserModel(Base):
    """用户的SQLAlchemy ORM模型"""
    __tablename__ = "users"
    
    username = Column(String, primary_key=True)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    sessions = relationship("SessionModel", back_populates="user", cascade="all, delete-orphan")
    devices = relationship("DeviceModel", back_populates="user", cascade="all, delete-orphan")
    
    def to_entity(self) -> User:
        """将ORM模型转换为领域实体"""
        return User(
            username=self.username,
            hashed_password=self.hashed_password,
        )


class SessionModel(Base):
    """会话的SQLAlchemy ORM模型"""
    __tablename__ = "sessions"
    
    session_key = Column(String, primary_key=True)
    username = Column(String, ForeignKey("users.username"), nullable=False)
    user_agent = Column(String)
    client_ip = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("UserModel", back_populates="sessions")
    
    def to_entity(self) -> Session:
        """将ORM模型转换为领域实体"""
        return Session(
            session_key=self.session_key,
            username=self.username,
            user_agent=self.user_agent,
            client_ip=ipaddress.ip_address(self.client_ip),
            created_at=self.created_at,
        )


class DeviceModel(Base):
    """设备的SQLAlchemy ORM模型"""
    __tablename__ = "devices"
    
    name = Column(String, primary_key=True)
    hashed_password = Column(String, nullable=False)
    username = Column(String, ForeignKey("users.username"), nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    
    user = relationship("UserModel", back_populates="devices")
    
    def to_entity(self) -> Device:
        """将ORM模型转换为领域实体"""
        return Device(
            name=self.name,
            hashed_password=self.hashed_password,
        )


# Pydantic模型，用于API请求和响应
class UserCreate(BaseModel):
    """用于创建用户的Pydantic模型"""
    username: str
    password: str


class UserLogin(BaseModel):
    """用于用户登录的Pydantic模型"""
    username: str
    password: str


class DeviceCreate(BaseModel):
    """用于创建设备的Pydantic模型"""
    name: str
    password: str


class DeviceResponse(BaseModel):
    """用于API响应的设备Pydantic模型"""
    name: str
    
    class Config:
        orm_mode = True


class SessionResponse(BaseModel):
    """用于API响应的会话Pydantic模型"""
    session_key: str
    
    class Config:
        orm_mode = True


# 添加新的Pydantic模型用于Web会话和Token认证
class UserSessionInfo(BaseModel):
    """用于Web会话中存储的用户信息"""
    id: str
    username: str
    is_superuser: bool = False
    
    class Config:
        orm_mode = True


class Token(BaseModel):
    """用于OAuth2 Token响应"""
    access_token: str
    token_type: str
    expires_in: int
    
    class Config:
        orm_mode = True 