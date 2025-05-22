from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated

from app.dependencies import get_progress_sync, get_auth_service
from app.service import ProgressSync
from app.entity.progress import ProgressRequest, ProgressResponse

router = APIRouter()

@router.put("/progress", response_model=ProgressResponse)
async def update_progress(
    progress: ProgressRequest,
    progress_sync: Annotated[ProgressSync, Depends(get_progress_sync)],
    device_name: str = Depends(get_device_name)
):
    """
    更新阅读进度
    
    此端点用于KOReader同步阅读进度。设备通过基本认证发送进度数据，
    服务器根据时间戳决定是否更新进度，并返回最新的进度数据。
    """
    # 添加设备名称
    progress_data = progress.model_dump()
    progress_data["auth_device_name"] = device_name
    
    # 同步进度
    result = await progress_sync.sync(None, progress_data)
    
    return result

@router.get("/progress/{document_id}", response_model=ProgressResponse)
async def fetch_progress(
    document_id: str,
    progress_sync: Annotated[ProgressSync, Depends(get_progress_sync)]
):
    """
    获取阅读进度
    
    根据文档ID获取最新的阅读进度。
    """
    result = await progress_sync.fetch(None, document_id)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到文档 {document_id} 的进度"
        )
    
    return result

# 依赖函数，用于从请求中获取设备名称
async def get_device_name(
    auth_service = Depends(get_auth_service)
):
    """
    从请求中获取设备名称
    
    此函数应该与认证中间件配合使用，获取已认证的设备名称。
    暂时返回一个默认值，后续实现完整的认证中间件后会更新。
    """
    # 暂时返回默认值，后续会通过认证中间件设置
    return "default_device" 