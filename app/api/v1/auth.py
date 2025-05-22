import logging
from fastapi import APIRouter, Depends, HTTPException, status, Request, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from typing import Annotated, Optional
from pydantic import BaseModel

from app.service.auth import AuthService
from app.dependencies import get_auth_service
from app.service import get_current_user

# 创建路由器
router = APIRouter()
logger = logging.getLogger(__name__)

# 用于文档的OAuth2方案
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/token")

# 模型定义
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    
class UserCreate(BaseModel):
    username: str
    password: str
    
class UserResponse(BaseModel):
    id: str
    username: str
    
class DeviceCreate(BaseModel):
    name: str


@router.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    """
    用户登录，获取访问令牌
    
    Args:
        form_data: 表单数据，包含用户名和密码
        auth_service: 认证服务
        
    Returns:
        TokenResponse: 访问令牌信息
    """
    # 验证用户名和密码
    try:
        user = await auth_service.authenticate_user(form_data.username, form_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名或密码不正确",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # 创建访问令牌
        access_token = auth_service.create_access_token(data={"sub": user.id})
        
        # 返回令牌信息
        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=auth_service.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    except Exception as e:
        logger.error(f"登录失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证失败",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post("/register", response_model=UserResponse)
async def register_user(
    user_create: UserCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    """
    注册新用户
    
    Args:
        user_create: 用户创建信息
        auth_service: 认证服务
        
    Returns:
        UserResponse: 用户信息
    """
    try:
        # 创建用户
        user = await auth_service.create_user(user_create.username, user_create.password)
        
        # 返回用户信息
        return UserResponse(
            id=user.id,
            username=user.username
        )
    except ValueError as e:
        # 用户名已存在
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"用户注册失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用户注册失败"
        )


@router.post("/logout")
async def logout(
    request: Request,
    response: Response,
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
):
    """
    用户登出
    
    Args:
        request: 请求对象
        response: 响应对象
        auth_service: 认证服务
        
    Returns:
        dict: 登出成功信息
    """
    # 清除会话
    request.session.clear()
    
    # 返回成功信息
    return {"message": "登出成功"}


@router.post("/devices", response_model=dict)
async def register_device(
    device_create: DeviceCreate,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    user_id: str = Depends(get_current_user)
):
    """
    注册新设备
    
    Args:
        device_create: 设备创建信息
        auth_service: 认证服务
        user_id: 用户ID
        
    Returns:
        dict: 设备信息，包含设备名称和密码
    """
    try:
        # 创建设备
        device_name, device_password = await auth_service.register_device(user_id, device_create.name)
        
        # 返回设备信息
        return {
            "name": device_name,
            "password": device_password,
            "message": "设备注册成功"
        }
    except ValueError as e:
        # 设备名已存在
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"设备注册失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="设备注册失败"
        )


@router.get("/devices")
async def list_devices(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    user_id: str = Depends(get_current_user)
):
    """
    获取用户设备列表
    
    Args:
        auth_service: 认证服务
        user_id: 用户ID
        
    Returns:
        list: 设备列表
    """
    try:
        # 获取设备列表
        devices = await auth_service.list_devices(user_id)
        
        # 返回设备列表
        return devices
    except Exception as e:
        logger.error(f"获取设备列表失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="获取设备列表失败"
        )


@router.delete("/devices/{device_name}")
async def delete_device(
    device_name: str,
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    user_id: str = Depends(get_current_user)
):
    """
    删除用户设备
    
    Args:
        device_name: 设备名称
        auth_service: 认证服务
        user_id: 用户ID
        
    Returns:
        dict: 删除成功信息
    """
    try:
        # 删除设备
        await auth_service.delete_device(user_id, device_name)
        
        # 返回成功信息
        return {"message": "设备删除成功"}
    except ValueError as e:
        # 设备不存在
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"删除设备失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="删除设备失败"
        )


@router.get("/me")
async def read_users_me(
    auth_service: Annotated[AuthService, Depends(get_auth_service)],
    user_id: str = Depends(get_current_user)
):
    """
    获取当前用户信息
    
    Args:
        auth_service: 认证服务
        user_id: 用户ID
        
    Returns:
        UserResponse: 用户信息
    """
    try:
        # 获取用户信息
        user = await auth_service.get_user(user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在"
            )
        
        # 返回用户信息
        return UserResponse(
            id=user.id,
            username=user.username
        )
    except Exception as e:
        logger.error(f"获取用户信息失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="获取用户信息失败"
        ) 