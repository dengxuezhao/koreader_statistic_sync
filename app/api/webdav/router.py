import logging
from fastapi import APIRouter, Depends, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse, PlainTextResponse
from typing import Annotated, Optional
import base64

from app.dependencies import get_auth_service
from app.service import AuthService


# 创建一个单独的路由器，不会被自动包含在API中
router = APIRouter()
logger = logging.getLogger(__name__)


# WebDAV基本认证中间件
async def basic_auth(
    request: Request, 
    auth_service: Annotated[AuthService, Depends(get_auth_service)]
) -> Optional[str]:
    """
    WebDAV基本认证中间件
    
    Args:
        request: FastAPI请求对象
        auth_service: 认证服务实例
        
    Returns:
        Optional[str]: 设备名称，如果认证失败则返回None
    """
    # 获取Authorization头
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Basic "):
        # 如果没有Authorization头，返回401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未认证",
            headers={"WWW-Authenticate": "Basic realm=\"KOmpanion WebDAV\""}
        )
    
    # 解码Basic认证
    device_name: str = ""
    password: str = ""
    try:
        auth_decoded = base64.b64decode(auth_header[6:]).decode("utf-8")
        device_name, password = auth_decoded.split(":", 1)
    except Exception as e:
        logger.error(f"解码Basic认证失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="认证格式无效",
            headers={"WWW-Authenticate": "Basic realm=\"KOmpanion WebDAV\""}
        )
    
    # 检查设备密码 (KOReader sends plain password for WebDAV Basic Auth, so plain=False)
    if not await auth_service.check_device_password(device_name, password, plain=False):
        # 如果密码不正确，返回401
        logger.warning(f"WebDAV authentication failed for device: {device_name}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码不正确",
            headers={"WWW-Authenticate": "Basic realm=\"KOmpanion WebDAV\""}
        )
    
    logger.info(f"WebDAV authentication successful for device: {device_name}")
    # 返回设备名称
    return device_name


@router.api_route("/", methods=["PROPFIND"])
async def propfind(
    request: Request,
    device_name: str = Depends(basic_auth)
):
    """
    处理PROPFIND请求
    
    WebDAV的PROPFIND方法用于获取资源的属性，包括目录列表。
    """
    logger.info(f"WebDAV PROPFIND请求: 设备={device_name}")
    
    # 返回一个静态的XML响应
    response = """<?xml version="1.0" encoding="UTF-8"?>
    <D:multistatus xmlns:D="DAV:">
    </D:multistatus>"""
    
    return Response(
        content=response,
        media_type="application/xml",
        status_code=status.HTTP_207_MULTI_STATUS
    )


@router.put("/statistics.sqlite3")
async def put_statistics(
    stats_service: Annotated[ReadingStats, Depends(get_reading_stats)],
    request: Request,
    device_name: str = Depends(basic_auth)
):
    """
    处理PUT请求，用于上传统计数据
    
    KOReader通过WebDAV上传statistics.sqlite3文件，该文件包含阅读统计数据。
    """
    logger.info(f"WebDAV PUT统计数据请求: 设备={device_name}")
    
    # 获取请求体（统计数据）
    body = await request.body()
    if not body:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": "请求体为空"}
        )
    
    try:
        # 将请求体传递给阅读统计服务
        await stats_service.write(None, request.stream(), device_name)
        
        # 返回成功响应
        return JSONResponse(
            status_code=status.HTTP_201_CREATED,
            content={"message": "统计数据已更新"}
        )
    except Exception as e:
        logger.error(f"写入统计数据失败: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"写入统计数据失败: {str(e)}"}
        )


@router.get("/statistics.sqlite3")
async def get_statistics(
    stats_service: Annotated[ReadingStats, Depends(get_reading_stats)],
    request: Request,
    device_name: str = Depends(basic_auth)
):
    """
    处理GET请求，用于下载统计数据
    
    KOReader可以通过WebDAV下载statistics.sqlite3文件，该文件包含阅读统计数据。
    """
    logger.info(f"WebDAV GET统计数据请求: 设备={device_name}")
    
    try:
        # 获取统计数据
        file_path = await stats_service.read(None, device_name)
        
        if not file_path:
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={"message": "未找到统计数据"}
            )
        
        # 返回文件
        return Response(
            content=open(file_path, "rb").read(),
            media_type="application/octet-stream"
        )
    except Exception as e:
        logger.error(f"读取统计数据失败: {str(e)}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": f"读取统计数据失败: {str(e)}"}
        ) 