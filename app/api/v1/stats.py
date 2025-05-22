import logging
from fastapi import APIRouter, Depends, HTTPException, status
from typing import Annotated, Optional, List, Dict, Any

from app.service.reading_stats import ReadingStats
from app.dependencies import get_reading_stats
from app.service import get_current_user

# 创建路由器
router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/")
async def get_reading_stats(
    book_id: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    reading_stats: Annotated[ReadingStats, Depends(get_reading_stats)] = None,
    user_id: str = Depends(get_current_user)
):
    """
    获取阅读统计数据
    
    Args:
        book_id: 书籍ID（可选）
        start_date: 开始日期（可选，格式：YYYY-MM-DD）
        end_date: 结束日期（可选，格式：YYYY-MM-DD）
        reading_stats: 阅读统计服务
        user_id: 用户ID
        
    Returns:
        dict: 阅读统计数据
    """
    try:
        # 获取统计数据
        stats = await reading_stats.get_statistics(user_id, book_id, start_date, end_date)
        
        # 返回统计数据
        return stats
    except Exception as e:
        logger.error(f"获取阅读统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取阅读统计失败: {str(e)}"
        )


@router.get("/summary")
async def get_reading_summary(
    period: str = "month",
    reading_stats: Annotated[ReadingStats, Depends(get_reading_stats)] = None,
    user_id: str = Depends(get_current_user)
):
    """
    获取阅读摘要
    
    Args:
        period: 统计周期（day/week/month/year）
        reading_stats: 阅读统计服务
        user_id: 用户ID
        
    Returns:
        dict: 阅读摘要数据
    """
    try:
        # 验证周期
        if period not in ["day", "week", "month", "year"]:
            raise ValueError("无效的统计周期")
        
        # 获取摘要数据
        summary = await reading_stats.get_summary(user_id, period)
        
        # 返回摘要数据
        return summary
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"获取阅读摘要失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取阅读摘要失败: {str(e)}"
        )


@router.get("/books/{book_id}")
async def get_book_stats(
    book_id: str,
    reading_stats: Annotated[ReadingStats, Depends(get_reading_stats)] = None,
    user_id: str = Depends(get_current_user)
):
    """
    获取指定书籍的阅读统计
    
    Args:
        book_id: 书籍ID
        reading_stats: 阅读统计服务
        user_id: 用户ID
        
    Returns:
        dict: 书籍阅读统计数据
    """
    try:
        # 获取书籍统计数据
        stats = await reading_stats.get_book_statistics(user_id, book_id)
        
        # 返回统计数据
        return stats
    except Exception as e:
        logger.error(f"获取书籍统计失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"未找到书籍或统计数据: {book_id}"
        )


@router.get("/trends")
async def get_reading_trends(
    metric: str = "reading_time",
    period: str = "week",
    last_n: int = 4,
    reading_stats: Annotated[ReadingStats, Depends(get_reading_stats)] = None,
    user_id: str = Depends(get_current_user)
):
    """
    获取阅读趋势
    
    Args:
        metric: 统计指标（reading_time/pages_read/completion_percentage）
        period: 统计周期（day/week/month/year）
        last_n: 最近的N个周期
        reading_stats: 阅读统计服务
        user_id: 用户ID
        
    Returns:
        dict: 阅读趋势数据
    """
    try:
        # 验证参数
        valid_metrics = ["reading_time", "pages_read", "completion_percentage"]
        if metric not in valid_metrics:
            raise ValueError(f"无效的统计指标，可选值: {', '.join(valid_metrics)}")
        
        valid_periods = ["day", "week", "month", "year"]
        if period not in valid_periods:
            raise ValueError(f"无效的统计周期，可选值: {', '.join(valid_periods)}")
        
        if last_n < 1 or last_n > 52:
            raise ValueError("last_n参数必须在1到52之间")
        
        # 获取趋势数据
        trends = await reading_stats.get_trends(user_id, metric, period, last_n)
        
        # 返回趋势数据
        return trends
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"获取阅读趋势失败: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"获取阅读趋势失败: {str(e)}"
        ) 