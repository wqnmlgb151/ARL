# -*- coding: utf-8 -*-
"""
ARL 基础仓库类
提供统一的数据库访问接口，自动集成 NoSQL 注入防护

用法：
    class TaskRepository(BaseRepository):
        collection_name = 'task'

    repo = TaskRepository()
    task = repo.find_one({'task_id': 'xxx'})
"""

from typing import Any, Dict, List, Optional

from app.database.connection import DatabaseManager
from app.utils.sanitizer import MongoSanitizer


class BaseRepository:
    """
    基础仓库类

    子类只需定义 collection_name 即可使用所有数据库操作。
    所有查询自动经过 MongoSanitizer 处理，防止 NoSQL 注入。
    """

    collection_name: str = ''

    def __init__(self):
        if not self.collection_name:
            raise ValueError(f"Subclass must define collection_name")

    def get_collection(self):
        """获取 MongoDB 集合"""
        return DatabaseManager.get_collection(self.collection_name)

    def _sanitize_query(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """清理查询条件（防止 NoSQL 注入）"""
        return MongoSanitizer.sanitize_query(query)

    def _sanitize_document(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """清理文档（防止 NoSQL 注入）"""
        return MongoSanitizer.sanitize_query(document)

    def find_one(self, query: Dict[str, Any]) -> Optional[Dict]:
        """
        查询单个文档（自动清理 NoSQL 注入）

        Args:
            query: 查询条件

        Returns:
            文档字典，未找到返回 None
        """
        clean_query = self._sanitize_query(query)
        return DatabaseManager.safe_find_one(self.collection_name, clean_query)

    def find(self, query: Dict[str, Any]) -> List[Dict]:
        """
        查询多个文档（自动清理 NoSQL 注入）

        Args:
            query: 查询条件

        Returns:
            文档列表
        """
        clean_query = self._sanitize_query(query)
        return DatabaseManager.safe_find(self.collection_name, clean_query)

    def insert_one(self, document: Dict[str, Any]) -> bool:
        """
        插入单个文档（自动清理 NoSQL 注入）

        Args:
            document: 要插入的文档

        Returns:
            是否插入成功
        """
        clean_doc = self._sanitize_document(document)
        return DatabaseManager.safe_insert_one(self.collection_name, clean_doc)

    def update_one(self, filter_query: Dict, update: Dict) -> bool:
        """
        更新单个文档（自动清理 NoSQL 注入）

        Args:
            filter_query: 过滤条件
            update: 更新内容

        Returns:
            是否更新成功
        """
        clean_filter = self._sanitize_query(filter_query)
        clean_update = self._sanitize_query(update)
        return DatabaseManager.safe_update_one(self.collection_name, clean_filter, clean_update)

    def delete_one(self, query: Dict[str, Any]) -> bool:
        """
        删除单个文档（自动清理 NoSQL 注入）

        Args:
            query: 删除条件

        Returns:
            是否删除成功
        """
        clean_query = self._sanitize_query(query)
        return DatabaseManager.safe_delete_one(self.collection_name, clean_query)

    def count(self, query: Dict[str, Any] = None) -> int:
        """
        统计文档数量

        Args:
            query: 过滤条件

        Returns:
            文档数量
        """
        collection = self.get_collection()
        if query is None:
            query = {}
        else:
            query = self._sanitize_query(query)
        return collection.count_documents(query)

    def find_many(self, query: Dict[str, Any], skip: int = 0, limit: int = 0) -> List[Dict]:
        """
        分页查询多个文档

        Args:
            query: 查询条件
            skip: 跳过数量
            limit: 限制数量

        Returns:
            文档列表
        """
        collection = self.get_collection()
        clean_query = self._sanitize_query(query)
        cursor = collection.find(clean_query).skip(skip).limit(limit)
        return list(cursor)

    def aggregate(self, pipeline: List[Dict]) -> List[Dict]:
        """
        聚合管道查询

        Args:
            pipeline: 聚合管道

        Returns:
            聚合结果列表
        """
        collection = self.get_collection()
        return list(collection.aggregate(pipeline))
