# -*- coding: utf-8 -*-
"""
ARL 数据库访问模块
提供统一的 MongoDB 集合访问接口，所有操作自动经过 NoSQL 注入防护

推荐用法：
    from app.utils.db import conn_db

    # 获取集合（已集成安全防护）
    task_col = conn_db('task')

    # 查询（自动清理 NoSQL 注入）
    task = task_col.find_one({'task_id': 'xxx'})
"""

from typing import Any, Dict, List, Optional

from app.config import Config
from app.utils.sanitizer import MongoSanitizer


class _SafeCollection:
    """
    安全的 MongoDB 集合代理

    包装原始 PyMongo Collection，所有读/写操作自动经过 MongoSanitizer 处理，
    防止 NoSQL 注入攻击。对于未拦截的操作（如 create_index），直接透传。
    """

    def __init__(self, collection):
        self._raw = collection

    # -- 透传未拦截的属性（name, full_name, create_index 等） --
    def __getattr__(self, name):
        if hasattr(self._raw, name):
            return getattr(self._raw, name)
        raise AttributeError(f"{type(self).__name__!r} has no attribute {name!r}")

    def find_one(self, filter=None, *args, **kwargs):
        clean = MongoSanitizer.sanitize_query(filter or {})
        return self._raw.find_one(clean, *args, **kwargs)

    def find(self, filter=None, *args, **kwargs):
        clean = MongoSanitizer.sanitize_query(filter or {})
        return self._raw.find(clean, *args, **kwargs)

    def insert_one(self, document, *args, **kwargs):
        clean = MongoSanitizer.sanitize_value(document)
        return self._raw.insert_one(clean, *args, **kwargs)

    def insert_many(self, documents, *args, **kwargs):
        clean_docs = [MongoSanitizer.sanitize_value(d) for d in documents]
        return self._raw.insert_many(clean_docs, *args, **kwargs)

    def update_one(self, filter, update, *args, **kwargs):
        clean_filter = MongoSanitizer.sanitize_query(filter)
        clean_update = MongoSanitizer.sanitize_value(update)
        return self._raw.update_one(clean_filter, clean_update, *args, **kwargs)

    def update_many(self, filter, update, *args, **kwargs):
        clean_filter = MongoSanitizer.sanitize_query(filter)
        clean_update = MongoSanitizer.sanitize_value(update)
        return self._raw.update_many(clean_filter, clean_update, *args, **kwargs)

    def delete_one(self, filter, *args, **kwargs):
        clean = MongoSanitizer.sanitize_query(filter)
        return self._raw.delete_one(clean, *args, **kwargs)

    def delete_many(self, filter, *args, **kwargs):
        clean = MongoSanitizer.sanitize_query(filter)
        return self._raw.delete_many(clean, *args, **kwargs)

    def count_documents(self, filter, *args, **kwargs):
        clean = MongoSanitizer.sanitize_query(filter)
        return self._raw.count_documents(clean, *args, **kwargs)

    def aggregate(self, pipeline, *args, **kwargs):
        clean_pipeline = [MongoSanitizer.sanitize_value(s) for s in pipeline]
        return self._raw.aggregate(clean_pipeline, *args, **kwargs)

    def bulk_write(self, requests, *args, **kwargs):
        clean_requests = [MongoSanitizer.sanitize_value(r) for r in requests]
        return self._raw.bulk_write(clean_requests, *args, **kwargs)

    def replace_one(self, filter, replacement, *args, **kwargs):
        clean_filter = MongoSanitizer.sanitize_query(filter)
        clean_replacement = MongoSanitizer.sanitize_value(replacement)
        return self._raw.replace_one(clean_filter, clean_replacement, *args, **kwargs)

    def find_one_and_replace(self, filter, replacement, *args, **kwargs):
        clean_filter = MongoSanitizer.sanitize_query(filter)
        clean_replacement = MongoSanitizer.sanitize_value(replacement)
        return self._raw.find_one_and_replace(clean_filter, clean_replacement, *args, **kwargs)

    def find_one_and_update(self, filter, update, *args, **kwargs):
        clean_filter = MongoSanitizer.sanitize_query(filter)
        clean_update = MongoSanitizer.sanitize_value(update)
        return self._raw.find_one_and_update(clean_filter, clean_update, *args, **kwargs)

    def find_one_and_delete(self, filter, *args, **kwargs):
        clean = MongoSanitizer.sanitize_query(filter)
        return self._raw.find_one_and_delete(clean, *args, **kwargs)

    def distinct(self, key, filter=None, *args, **kwargs):
        clean = MongoSanitizer.sanitize_query(filter or {})
        return self._raw.distinct(key, clean, *args, **kwargs)


def conn_db(collection: str, db_name: Optional[str] = None) -> _SafeCollection:
    """
    获取 MongoDB 集合（统一入口，自动集成 NoSQL 注入防护）

    Args:
        collection: 集合名称
        db_name: 数据库名称（可选，默认从 Config 读取）

    Returns:
        安全包装后的 MongoDB 集合对象

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

    raw_collection = DatabaseManager.get_collection(collection, db_name)
    return _SafeCollection(raw_collection)


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
