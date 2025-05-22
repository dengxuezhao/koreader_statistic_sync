from typing import Optional
from sqlalchemy import Column, String, Float, BigInteger, DateTime, func
from pydantic import BaseModel

from app.database import Base


class Progress:
    """
    阅读进度实体，表示KOReader同步的阅读进度数据。
    这是一个领域模型类，独立于ORM或数据库实现。
    """
    def __init__(
        self, 
        document: str,
        percentage: float,
        progress: str,
        device: str,
        device_id: str,
        timestamp: int,
        auth_device_name: str = ""
    ):
        self.document = document        # 文档ID (md5 hash)
        self.percentage = percentage    # 阅读进度百分比 (0-100)
        self.progress = progress        # 进度标记 (如页码或位置)
        self.device = device            # 设备名称
        self.device_id = device_id      # 设备ID
        self.timestamp = timestamp      # 时间戳 (Unix时间戳)
        self.auth_device_name = auth_device_name  # 认证设备名称


# SQLAlchemy ORM模型
class ProgressModel(Base):
    """阅读进度的SQLAlchemy ORM模型"""
    __tablename__ = "progress"
    
    id = Column(String, primary_key=True)
    document = Column(String, index=True)
    percentage = Column(Float)
    progress = Column(String)
    device = Column(String)
    device_id = Column(String)
    timestamp = Column(BigInteger)
    auth_device_name = Column(String)
    created_at = Column(DateTime, server_default=func.now())
    
    def to_entity(self) -> Progress:
        """将ORM模型转换为领域实体"""
        return Progress(
            document=self.document,
            percentage=self.percentage,
            progress=self.progress,
            device=self.device,
            device_id=self.device_id,
            timestamp=self.timestamp,
            auth_device_name=self.auth_device_name
        )


# Pydantic模型，用于API请求和响应
class ProgressRequest(BaseModel):
    """用于同步进度API请求的Pydantic模型"""
    document: str
    percentage: float
    progress: str
    device: str
    device_id: str
    timestamp: int


class ProgressResponse(BaseModel):
    """用于同步进度API响应的Pydantic模型"""
    document: str
    percentage: float
    progress: str
    device: str
    device_id: str
    timestamp: int
    
    class Config:
        orm_mode = True 