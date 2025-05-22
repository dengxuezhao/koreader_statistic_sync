import ipaddress
import uuid
from abc import ABC, abstractmethod
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import update, delete

from app.entity.user import (
    User, Device, Session, 
    UserModel, DeviceModel, SessionModel,
    UserNotFoundError, UserAlreadyExistsError,
    SessionNotFoundError, DeviceNotFoundError, DeviceAlreadyExistsError
)


class UserRepo(ABC):
    """用户存储库接口"""
    
    @abstractmethod
    async def create_user(self, user: User) -> None:
        """
        创建新用户
        
        Args:
            user: 用户实体
            
        Raises:
            UserAlreadyExistsError: 用户已存在时抛出
        """
        pass
    
    @abstractmethod
    async def get_user_by_username(self, username: str) -> User:
        """
        通过用户名获取用户
        
        Args:
            username: 用户名
            
        Returns:
            用户实体
            
        Raises:
            UserNotFoundError: 用户不存在时抛出
        """
        pass
    
    @abstractmethod
    async def get_user_by_session(self, session_key: str) -> User:
        """
        通过会话密钥获取用户
        
        Args:
            session_key: 会话密钥
            
        Returns:
            用户实体
            
        Raises:
            SessionNotFoundError: 会话不存在时抛出
            UserNotFoundError: 用户不存在时抛出
        """
        pass
    
    @abstractmethod
    async def store_session(
        self, 
        username: str, 
        session_key: str, 
        user_agent: str, 
        client_ip: ipaddress.IPv4Address
    ) -> None:
        """
        存储用户会话
        
        Args:
            username: 用户名
            session_key: 会话密钥
            user_agent: 用户代理
            client_ip: 客户端IP地址
            
        Raises:
            UserNotFoundError: 用户不存在时抛出
        """
        pass
    
    @abstractmethod
    async def delete_session(self, session_key: str) -> None:
        """
        删除会话
        
        Args:
            session_key: 会话密钥
            
        Raises:
            SessionNotFoundError: 会话不存在时抛出
        """
        pass
    
    @abstractmethod
    async def create_device(self, device: Device) -> None:
        """
        创建设备
        
        Args:
            device: 设备实体
            
        Raises:
            DeviceAlreadyExistsError: 设备已存在时抛出
        """
        pass
    
    @abstractmethod
    async def get_device_by_name(self, device_name: str) -> Device:
        """
        通过名称获取设备
        
        Args:
            device_name: 设备名称
            
        Returns:
            设备实体
            
        Raises:
            DeviceNotFoundError: 设备不存在时抛出
        """
        pass
    
    @abstractmethod
    async def delete_device(self, device_name: str) -> None:
        """
        删除设备
        
        Args:
            device_name: 设备名称
            
        Raises:
            DeviceNotFoundError: 设备不存在时抛出
        """
        pass
    
    @abstractmethod
    async def list_devices(self) -> List[Device]:
        """
        列出所有设备
        
        Returns:
            设备列表
        """
        pass


class UserDatabaseRepo(UserRepo):
    """PostgreSQL用户存储库实现"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def create_user(self, user: User) -> None:
        """创建新用户"""
        # 检查用户是否已存在
        stmt = select(UserModel).where(UserModel.username == user.username)
        result = await self.db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        
        if existing_user:
            raise UserAlreadyExistsError(f"User {user.username} already exists")
        
        # 创建新用户
        db_user = UserModel(
            username=user.username,
            hashed_password=user.hashed_password
        )
        
        self.db.add(db_user)
        await self.db.commit()
    
    async def get_user_by_username(self, username: str) -> User:
        """通过用户名获取用户"""
        stmt = select(UserModel).where(UserModel.username == username)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise UserNotFoundError(f"User {username} not found")
        
        return user.to_entity()
    
    async def get_user_by_session(self, session_key: str) -> User:
        """通过会话密钥获取用户"""
        # 查找会话
        stmt = select(SessionModel).where(SessionModel.session_key == session_key)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            raise SessionNotFoundError(f"Session {session_key} not found")
        
        # 查找用户
        stmt = select(UserModel).where(UserModel.username == session.username)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise UserNotFoundError(f"User {session.username} not found")
        
        return user.to_entity()
    
    async def store_session(
        self, 
        username: str, 
        session_key: str, 
        user_agent: str, 
        client_ip: ipaddress.IPv4Address
    ) -> None:
        """存储用户会话"""
        # 检查用户是否存在
        stmt = select(UserModel).where(UserModel.username == username)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise UserNotFoundError(f"User {username} not found")
        
        # 创建会话
        session = SessionModel(
            session_key=session_key,
            username=username,
            user_agent=user_agent,
            client_ip=str(client_ip)
        )
        
        self.db.add(session)
        await self.db.commit()
    
    async def delete_session(self, session_key: str) -> None:
        """删除会话"""
        # 检查会话是否存在
        stmt = select(SessionModel).where(SessionModel.session_key == session_key)
        result = await self.db.execute(stmt)
        session = result.scalar_one_or_none()
        
        if not session:
            raise SessionNotFoundError(f"Session {session_key} not found")
        
        # 删除会话
        stmt = delete(SessionModel).where(SessionModel.session_key == session_key)
        await self.db.execute(stmt)
        await self.db.commit()
    
    async def create_device(self, device: Device) -> None:
        """创建设备"""
        # 检查设备是否已存在
        stmt = select(DeviceModel).where(DeviceModel.name == device.name)
        result = await self.db.execute(stmt)
        existing_device = result.scalar_one_or_none()
        
        if existing_device:
            raise DeviceAlreadyExistsError(f"Device {device.name} already exists")
        
        # 创建设备（默认关联到第一个用户）
        stmt = select(UserModel)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()
        
        if not user:
            raise UserNotFoundError("No user found to associate device with")
        
        # 创建设备
        db_device = DeviceModel(
            name=device.name,
            hashed_password=device.hashed_password,
            username=user.username
        )
        
        self.db.add(db_device)
        await self.db.commit()
    
    async def get_device_by_name(self, device_name: str) -> Device:
        """通过名称获取设备"""
        stmt = select(DeviceModel).where(DeviceModel.name == device_name)
        result = await self.db.execute(stmt)
        device = result.scalar_one_or_none()
        
        if not device:
            raise DeviceNotFoundError(f"Device {device_name} not found")
        
        return device.to_entity()
    
    async def delete_device(self, device_name: str) -> None:
        """删除设备"""
        # 检查设备是否存在
        stmt = select(DeviceModel).where(DeviceModel.name == device_name)
        result = await self.db.execute(stmt)
        device = result.scalar_one_or_none()
        
        if not device:
            raise DeviceNotFoundError(f"Device {device_name} not found")
        
        # 删除设备
        stmt = delete(DeviceModel).where(DeviceModel.name == device_name)
        await self.db.execute(stmt)
        await self.db.commit()
    
    async def list_devices(self) -> List[Device]:
        """列出所有设备"""
        stmt = select(DeviceModel)
        result = await self.db.execute(stmt)
        devices = result.scalars().all()
        
        return [device.to_entity() for device in devices]


class MemoryUserRepo(UserRepo):
    """内存用户存储库实现（用于测试和开发）"""
    
    def __init__(self):
        self._users = {}  # username -> User
        self._sessions = {}  # session_key -> Session
        self._devices = {}  # device_name -> Device
    
    async def create_user(self, user: User) -> None:
        """创建新用户"""
        if user.username in self._users:
            raise UserAlreadyExistsError(f"User {user.username} already exists")
        
        self._users[user.username] = user
    
    async def get_user_by_username(self, username: str) -> User:
        """通过用户名获取用户"""
        if username not in self._users:
            raise UserNotFoundError(f"User {username} not found")
        
        return self._users[username]
    
    async def get_user_by_session(self, session_key: str) -> User:
        """通过会话密钥获取用户"""
        if session_key not in self._sessions:
            raise SessionNotFoundError(f"Session {session_key} not found")
        
        session = self._sessions[session_key]
        
        if session.username not in self._users:
            raise UserNotFoundError(f"User {session.username} not found")
        
        return self._users[session.username]
    
    async def store_session(
        self, 
        username: str, 
        session_key: str, 
        user_agent: str, 
        client_ip: ipaddress.IPv4Address
    ) -> None:
        """存储用户会话"""
        if username not in self._users:
            raise UserNotFoundError(f"User {username} not found")
        
        session = Session(
            session_key=session_key,
            username=username,
            user_agent=user_agent,
            client_ip=client_ip
        )
        
        self._sessions[session_key] = session
    
    async def delete_session(self, session_key: str) -> None:
        """删除会话"""
        if session_key not in self._sessions:
            raise SessionNotFoundError(f"Session {session_key} not found")
        
        del self._sessions[session_key]
    
    async def create_device(self, device: Device) -> None:
        """创建设备"""
        if device.name in self._devices:
            raise DeviceAlreadyExistsError(f"Device {device.name} already exists")
        
        self._devices[device.name] = device
    
    async def get_device_by_name(self, device_name: str) -> Device:
        """通过名称获取设备"""
        if device_name not in self._devices:
            raise DeviceNotFoundError(f"Device {device_name} not found")
        
        return self._devices[device_name]
    
    async def delete_device(self, device_name: str) -> None:
        """删除设备"""
        if device_name not in self._devices:
            raise DeviceNotFoundError(f"Device {device_name} not found")
        
        del self._devices[device_name]
    
    async def list_devices(self) -> List[Device]:
        """列出所有设备"""
        return list(self._devices.values()) 