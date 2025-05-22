from typing import List, Generic, TypeVar, Dict, Any

# 定义类型变量，用于泛型
T = TypeVar('T')


class PaginatedList(Generic[T]):
    """
    分页列表类，用于API响应的分页。
    
    类型参数:
        T: 列表项的类型
    """
    
    def __init__(
        self, 
        items: List[T], 
        per_page: int, 
        current_page: int, 
        total_count: int
    ):
        """
        初始化分页列表
        
        Args:
            items: 当前页的项目列表
            per_page: 每页项目数量
            current_page: 当前页码（从1开始）
            total_count: 总项目数量
        """
        self.items = items
        self.per_page = per_page
        self.current_page = current_page
        self.total_count = total_count
    
    def total_pages(self) -> int:
        """
        计算总页数
        
        Returns:
            int: 总页数
        """
        if self.total_count == 0:
            return 0
        # 向上取整
        return (self.total_count + self.per_page - 1) // self.per_page
    
    def has_next(self) -> bool:
        """
        检查是否有下一页
        
        Returns:
            bool: 如果有下一页则返回True，否则返回False
        """
        return self.current_page < self.total_pages()
    
    def has_prev(self) -> bool:
        """
        检查是否有上一页
        
        Returns:
            bool: 如果有上一页则返回True，否则返回False
        """
        return self.current_page > 1
    
    def first_page(self) -> int:
        """
        获取第一页的页码
        
        Returns:
            int: 第一页的页码（1）
        """
        return 1
    
    def last_page(self) -> int:
        """
        获取最后一页的页码
        
        Returns:
            int: 最后一页的页码
        """
        return self.total_pages()
    
    def next_page(self) -> int:
        """
        获取下一页的页码
        
        Returns:
            int: 下一页的页码，如果已经是最后一页则返回当前页码
        """
        if self.has_next():
            return self.current_page + 1
        return self.current_page
    
    def prev_page(self) -> int:
        """
        获取上一页的页码
        
        Returns:
            int: 上一页的页码，如果已经是第一页则返回当前页码
        """
        if self.has_prev():
            return self.current_page - 1
        return self.current_page
    
    def to_dict(self) -> Dict[str, Any]:
        """
        将分页信息转换为字典，用于API响应
        
        Returns:
            Dict[str, Any]: 包含分页信息的字典
        """
        return {
            "items": self.items,
            "pagination": {
                "current_page": self.current_page,
                "per_page": self.per_page,
                "total_count": self.total_count,
                "total_pages": self.total_pages(),
                "has_next": self.has_next(),
                "has_prev": self.has_prev(),
                "next_page": self.next_page(),
                "prev_page": self.prev_page()
            }
        }


# 创建书籍列表的特定分页类型（用于类型提示）
class PaginatedBookList(PaginatedList):
    """
    书籍列表的分页类型
    这是一个类型别名，用于类型提示
    """
    pass 