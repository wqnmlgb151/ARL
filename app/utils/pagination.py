# -*- coding: utf-8 -*-
"""
ARL 分页工具模块
提供统一的分页查询和响应格式
"""

import math
from typing import Any, Optional, Dict, List, Tuple
from dataclasses import dataclass

from flask import request


@dataclass
class PaginationParams:
    """分页参数"""
    page: int = 1           # 当前页码（从1开始）
    size: int = 20          # 每页大小
    max_size: int = 1000    # 最大每页大小

    def __post_init__(self):
        # 确保参数有效
        self.page = max(1, self.page)
        self.size = max(1, min(self.size, self.max_size))

    @property
    def skip(self) -> int:
        """跳过的记录数"""
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        """返回的记录数"""
        return self.size


@dataclass
class PaginationInfo:
    """分页信息（用于响应）"""
    page: int
    size: int
    total: int
    pages: int
    has_next: bool
    has_prev: bool

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "page": self.page,
            "size": self.size,
            "total": self.total,
            "pages": self.pages,
            "has_next": self.has_next,
            "has_prev": self.has_prev
        }


@dataclass
class PaginatedResponse:
    """分页响应"""
    data: List[Any]
    pagination: PaginationInfo

    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "data": self.data,
            "pagination": self.pagination.to_dict()
        }


def get_pagination_params(
    page: Optional[int] = None,
    size: Optional[int] = None,
    max_size: int = 1000
) -> PaginationParams:
    """
    从请求中获取分页参数

    Args:
        page: 页码，如果为 None 则从请求参数获取
        size: 每页大小，如果为 None 则从请求参数获取
        max_size: 最大每页大小

    Returns:
        PaginationParams 对象
    """
    if page is None:
        try:
            page = int(request.args.get('page', 1))
        except (ValueError, TypeError):
            page = 1

    if size is None:
        try:
            size = int(request.args.get('size', request.args.get('limit', 20)))
        except (ValueError, TypeError):
            size = 20

    return PaginationParams(page=page, size=size, max_size=max_size)


def paginate_cursor(
    cursor,
    page: int = 1,
    size: int = 20,
    total: Optional[int] = None
) -> PaginatedResponse:
    """
    对查询结果进行分页（使用 skip/limit）

    Args:
        cursor: MongoDB 查询游标
        page: 页码
        size: 每页大小
        total: 总数（如果为 None 则查询总数）

    Returns:
        PaginatedResponse 对象
    """
    params = PaginationParams(page=page, size=size)

    # 获取总数
    if total is None:
        try:
            total = cursor.count()
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception(f"Error in {__name__}: {e}")
            # Log error but default to 0 to allow pagination to continue
            import logging
            logging.getLogger(__name__).warning(f"Failed to get cursor count: {e}")
            total = 0

    # 计算总页数
    pages = math.ceil(total / size) if total > 0 else 0

    # 获取分页数据
    data = list(cursor.skip(params.skip).limit(params.limit))

    # 构建分页信息
    pagination = PaginationInfo(
        page=params.page,
        size=params.size,
        total=total,
        pages=pages,
        has_next=params.page < pages,
        has_prev=params.page > 1
    )

    return PaginatedResponse(data=data, pagination=pagination)


def paginate_list(
    data: List[Any],
    page: int = 1,
    size: int = 20
) -> PaginatedResponse:
    """
    对列表进行分页

    Args:
        data: 完整数据列表
        page: 页码
        size: 每页大小

    Returns:
        PaginatedResponse 对象
    """
    params = PaginationParams(page=page, size=size)
    total = len(data)
    pages = math.ceil(total / size) if total > 0 else 0

    # 切片获取分页数据
    start = params.skip
    end = start + params.limit
    page_data = data[start:end]

    # 构建分页信息
    pagination = PaginationInfo(
        page=params.page,
        size=params.size,
        total=total,
        pages=pages,
        has_next=params.page < pages,
        has_prev=params.page > 1
    )

    return PaginatedResponse(data=page_data, pagination=pagination)


def paginate_response(
    data: List[Any],
    page: int = 1,
    size: int = 20,
    total: Optional[int] = None
) -> Dict[str, Any]:
    """
    构建分页响应字典（简化版）

    Args:
        data: 数据列表
        page: 页码
        size: 每页大小
        total: 总数

    Returns:
        响应字典
    """
    if total is None:
        total = len(data)

    params = PaginationParams(page=page, size=size)
    pages = math.ceil(total / size) if total > 0 else 0

    return {
        "code": 0,
        "message": "success",
        "success": True,
        "data": data,
        "pagination": {
            "page": params.page,
            "size": params.size,
            "total": total,
            "pages": pages,
            "has_next": params.page < pages,
            "has_prev": params.page > 1
        }
    }


class CursorPaginator:
    """
    游标分页器（适用于大数据集）
    使用 last_id 代替 skip，性能更好
    """

    def __init__(self, collection, query: dict = None, sort_field: str = "_id",
                 sort_order: int = -1):
        """
        初始化游标分页器

        Args:
            collection: MongoDB 集合
            query: 查询条件
            sort_field: 排序字段
            sort_order: 排序方向（1升序，-1降序）
        """
        self.collection = collection
        self.query = query or {}
        self.sort_field = sort_field
        self.sort_order = sort_order

    def paginate(
        self,
        cursor_value: Any = None,
        size: int = 20,
        direction: str = "next"
    ) -> Tuple[List[dict], bool, Optional[Any]]:
        """
        获取一页数据

        Args:
            cursor_value: 游标值（上一页最后一条记录的排序字段值）
            size: 每页大小
            direction: 方向（next/prev）

        Returns:
            (数据列表, 是否有更多, 下一页游标)
        """
        query = dict(self.query)

        if cursor_value is not None:
            if direction == "next":
                query[self.sort_field] = {"$gt" if self.sort_order > 0 else "$lt": cursor_value}
            else:
                query[self.sort_field] = {"$lt" if self.sort_order > 0 else "$gt": cursor_value}

        # 查询数据（多取一条判断是否有更多）
        cursor = self.collection.find(query).sort(
            self.sort_field, self.sort_order
        ).limit(size + 1)

        data = list(cursor)
        has_more = len(data) > size

        if has_more:
            data = data[:size]

        next_cursor = None
        if data and has_more:
            next_cursor = data[-1].get(self.sort_field)

        return data, has_more, next_cursor
