import hashlib
import ipaddress
import uuid
import logging
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from passlib.context import CryptContext
from fastapi import Request, HTTPException, status

from app.entity.user import (
    User, Device, 
    IncorrectPasswordError, 
    UserAlreadyExistsError,
    UserSessionInfo
)
from app.repository.user_repo import UserRepo
from app.config import Settings


class AuthService:
    """认证服务，处理用户认证和会话管理"""
    
    def __init__(self, user_repo: UserRepo, settings: Settings):
        self.user_repo = user_repo
        self.settings = settings
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.logger = logging.getLogger(__name__)
    
    async def register_user(self, username: str, password: str) -> None:
        """
        注册新用户
        
        Args:
            username: 用户名
            password: 密码
            
        Raises:
            UserAlreadyExistsError: 用户已存在时抛出
        """
        hashed_password = self._hash_password(password)
        user = User(username=username, hashed_password=hashed_password)
        
        try:
            await self.user_repo.create_user(user)
            self.logger.info(f"User {username} registered successfully")
        except UserAlreadyExistsError:
            self.logger.warning(f"Attempted to register existing user: {username}")
            # 已存在的情况下，尝试验证密码
            existing_user = await self.user_repo.get_user_by_username(username)
            if not self._verify_password(password, existing_user.hashed_password):
                raise IncorrectPasswordError(f"Incorrect password for user {username}")
    
    async def check_password(self, username: str, password: str) -> bool:
        """
        检查用户密码是否正确
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            如果密码正确则返回True，否则返回False
        """
        try:
            user = await self.user_repo.get_user_by_username(username)
            return self._verify_password(password, user.hashed_password)
        except Exception as e:
            self.logger.error(f"Error checking password for user {username}: {str(e)}")
            return False
    
    async def login(
        self, 
        username: str, 
        password: str, 
        user_agent: str, 
        client_ip: ipaddress.IPv4Address
    ) -> str:
        """
        用户登录
        
        Args:
            username: 用户名
            password: 密码
            user_agent: 用户代理
            client_ip: 客户端IP地址
            
        Returns:
            会话密钥
            
        Raises:
            IncorrectPasswordError: 密码不正确时抛出
        """
        user = await self.user_repo.get_user_by_username(username)
        
        if not self._verify_password(password, user.hashed_password):
            self.logger.warning(f"Failed login attempt for user {username}")
            raise IncorrectPasswordError(f"Incorrect password for user {username}")
        
        # 创建会话
        session_key = str(uuid.uuid4())
        await self.user_repo.store_session(username, session_key, user_agent, client_ip)
        self.logger.info(f"User {username} logged in successfully")
        
        return session_key
    
    async def logout(self, session_key: str) -> None:
        """
        用户登出
        
        Args:
            session_key: 会话密钥
        """
        try:
            await self.user_repo.delete_session(session_key)
            self.logger.info(f"Session {session_key} deleted successfully")
        except Exception as e:
            self.logger.error(f"Error logging out session {session_key}: {str(e)}")
    
    async def is_authenticated(self, session_key: str) -> bool:
        """
        检查用户是否已认证
        
        Args:
            session_key: 会话密钥
            
        Returns:
            如果用户已认证则返回True，否则返回False
        """
        try:
            await self.user_repo.get_user_by_session(session_key)
            return True
        except Exception as e:
            self.logger.debug(f"Session authentication check failed: {str(e)}")
            return False
    
    async def add_user_device(self, device_name: str, password: str) -> None:
        """
        添加用户设备
        
        Args:
            device_name: 设备名称
            password: 设备密码
        """
        # KOReader使用MD5哈希密码
        hashed_password = self._hash_sync_password(password)
        device = Device(name=device_name, hashed_password=hashed_password)
        
        await self.user_repo.create_device(device)
        self.logger.info(f"Device {device_name} added successfully")
    
    async def deactivate_user_device(self, device_name: str) -> None:
        """
        停用用户设备
        
        Args:
            device_name: 设备名称
        """
        await self.user_repo.delete_device(device_name)
        self.logger.info(f"Device {device_name} deactivated successfully")
    
    async def check_device_password(
        self, 
        device_name: str, 
        password: str, 
        plain: bool = False
    ) -> bool:
        """
        检查设备密码是否正确
        
        Args:
            device_name: 设备名称
            password: 设备密码
            plain: 如果为True，则密码已经是MD5哈希
            
        Returns:
            如果密码正确则返回True，否则返回False
        """
        try:
            device = await self.user_repo.get_device_by_name(device_name)
            
            if plain:
                to_check = password
            else:
                to_check = self._hash_sync_password(password)
            
            return device.hashed_password == to_check
        except Exception as e:
            self.logger.error(f"Error checking device password: {str(e)}")
            return False
    
    async def list_devices(self):
        """
        列出所有设备
        
        Returns:
            设备列表
        """
        return await self.user_repo.list_devices()
    
    def _hash_password(self, password: str) -> str:
        """使用bcrypt哈希密码"""
        return self.pwd_context.hash(password)
    
    def _verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """验证密码"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def _hash_sync_password(self, password: str) -> str:
        """
        使用MD5哈希密码（KOReader同步兼容）
        """
        return hashlib.md5(password.encode()).hexdigest()

    async def authenticate_admin_via_config(self, username: str, password: str) -> Optional[UserSessionInfo]:
        """
        Authenticates the admin user based on configuration settings (plain text password).
        """
        admin_username = self.settings.AUTH_USERNAME
        admin_password = self.settings.AUTH_PASSWORD

        self.logger.debug(f"Attempting admin authentication for user: {username} via config.")
        if username == admin_username and password == admin_password:
            self.logger.info(f"Admin user {username} authenticated successfully via config.")
            return UserSessionInfo(id="config_admin_001", username=username, is_superuser=True)
        else:
            self.logger.warning(f"Admin authentication failed for user: {username} via config. Credentials did not match.")
            return None


# FastAPI依赖函数，用于从请求中获取当前认证用户
async def get_current_user(request: Request, auth_service: AuthService):
    """
    从请求中获取当前认证用户
    
    Args:
        request: FastAPI请求对象
        auth_service: 认证服务实例
        
    Returns:
        用户名
        
    Raises:
        HTTPException: 用户未认证时抛出
    """
    session_key = request.session.get("session_key")
    
    if not session_key or not await auth_service.is_authenticated(session_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = await auth_service.user_repo.get_user_by_session(session_key)
    return user.username 