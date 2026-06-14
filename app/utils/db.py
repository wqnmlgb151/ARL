# -*- coding: utf-8 -*-
"""
ARL 数据库访问模块
提供统一的 MongoDB 集合访问接口

推荐用法：
    from app.utils.db import conn_db

    # 获取集合
    task_col = conn_db('task')

    # 查询
    task = task_col.find_one({'task_id': 'xxx'})
"""

from typing import Optional

from app.config import Config


def conn_db(collection: str, db_name: Optional[str] = None):
    """
    获取 MongoDB 集合（统一入口）

    Args:
        collection: 集合名称
        db_name: 数据库名称（可选，默认从 Config 读取）

    Returns:
        MongoDB 集合对象

    Raises:
        RuntimeError: 数据库未初始化时抛出异常
    """
    # 导入 DatabaseManager（延迟导入避免循环依赖）
    from app.database.connection import DatabaseManager

    if not DatabaseManager.is_initialized():
        # 自动初始化（向后兼容）
        try:
            DatabaseManager.init()
        except Exception as e:
            raise RuntimeError(f"Database initialization failed: {e}") from e

    return DatabaseManager.get_collection(collection, db_name)


def get_db(db_name: Optional[str] = None):
    """
    获取 MongoDB 数据库实例

    Args:
        db_name: 数据库名称（可选）

    Returns:
        MongoDB 数据库对象
    """
    from app.database.connection import DatabaseManager

    if not DatabaseManager.is_initialized():
        DatabaseManager.init()

    return DatabaseManager.get_db(db_name)


def init_db(mongo_url: Optional[str] = None, db_name: Optional[str] = None) -> None:
    """
    初始化数据库连接

    Args:
        mongo_url: MongoDB 连接 URL
        db_name: 数据库名称
    """
    from app.database.connection import DatabaseManager
    DatabaseManager.init(mongo_url, db_name)
