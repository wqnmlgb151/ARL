# -*- coding: utf-8 -*-
"""
ARL统一数据库连接管理器
提供单例模式的MongoDB连接，支持索引创建和连接池配置
集成 NoSQL 注入防护
"""

import logging
from typing import Any, Dict, List, Optional

from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

from app.config import Config
from app.utils.sanitizer import MongoSanitizer

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    MongoDB数据库管理器（单例模式）

    特性：
    - 线程安全的单例实现
    - 连接池配置优化
    - 自动索引创建
    - 统一的集合访问接口

    用法：
        # 初始化（应用启动时调用一次）
        DatabaseManager.init()

        # 获取集合
        task_col = DatabaseManager.get_collection('task')

        # 获取数据库实例
        db = DatabaseManager.get_db()
    """

    _instance: Optional['DatabaseManager'] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None

    @classmethod
    def init(cls, mongo_url: Optional[str] = None, db_name: Optional[str] = None) -> None:
        """
        初始化数据库连接

        Args:
            mongo_url: MongoDB连接URL，默认从Config读取
            db_name: 数据库名称，默认从Config读取

        Raises:
            RuntimeError: 重复初始化时抛出异常
        """
        if cls._client is not None:
            raise RuntimeError("DatabaseManager already initialized. Call close() first.")

        url = mongo_url or Config.MONGO_URL
        name = db_name or Config.MONGO_DB

        logger.info(f"Connecting to MongoDB: {url}")

        cls._client = MongoClient(
            url,
            maxPoolSize=100,
            minPoolSize=20,
            maxIdleTimeMS=30000,
            connectTimeoutMS=5000,
            serverSelectionTimeoutMS=5000,
            retryWrites=True,
            retryReads=True
        )

        cls._db = cls._client[name]
        cls._instance = cls()

        # 创建索引
        cls._create_indexes()

        logger.info(f"Database initialized: {name}")

    @classmethod
    def _create_indexes(cls) -> None:
        """创建数据库索引以优化查询性能"""
        if cls._db is None:
            return

        index_config = {
            'task': [
                {'keys': [('status', ASCENDING)], 'name': 'idx_task_status'},
                {'keys': [('target', ASCENDING)], 'name': 'idx_task_target'},
                {'keys': [('created_at', DESCENDING)], 'name': 'idx_task_created_at'},
                {'keys': [('status', ASCENDING), ('created_at', DESCENDING)], 'name': 'idx_task_status_created'},
                {'keys': [('task_id', ASCENDING)], 'name': 'idx_task_task_id', 'unique': True},
            ],
            'domain': [
                {'keys': [('domain', ASCENDING)], 'name': 'idx_domain_domain', 'unique': True},
                {'keys': [('ip', ASCENDING)], 'name': 'idx_domain_ip'},
                {'keys': [('task_id', ASCENDING)], 'name': 'idx_domain_task_id'},
                {'keys': [('domain', ASCENDING), ('ip', ASCENDING)], 'name': 'idx_domain_domain_ip'},
            ],
            'ip': [
                {'keys': [('ip', ASCENDING)], 'name': 'idx_ip_ip', 'unique': True},
                {'keys': [('task_id', ASCENDING)], 'name': 'idx_ip_task_id'},
                {'keys': [('status', ASCENDING)], 'name': 'idx_ip_status'},
            ],
            'site': [
                {'keys': [('url', ASCENDING)], 'name': 'idx_site_url'},
                {'keys': [('task_id', ASCENDING)], 'name': 'idx_site_task_id'},
                {'keys': [('status', ASCENDING)], 'name': 'idx_site_status'},
                {'keys': [('task_id', ASCENDING), ('status', ASCENDING)], 'name': 'idx_site_task_status'},
            ],
            'cert': [
                {'keys': [('serial_number', ASCENDING)], 'name': 'idx_cert_serial'},
                {'keys': [('task_id', ASCENDING)], 'name': 'idx_cert_task_id'},
            ],
            'scheduler': [
                {'keys': [('task_id', ASCENDING)], 'name': 'idx_scheduler_task_id'},
                {'keys': [('status', ASCENDING)], 'name': 'idx_scheduler_status'},
                {'keys': [('next_run', ASCENDING)], 'name': 'idx_scheduler_next_run'},
            ],
            'url': [
                {'keys': [('url', ASCENDING)], 'name': 'idx_url_url'},
                {'keys': [('task_id', ASCENDING)], 'name': 'idx_url_task_id'},
                {'keys': [('task_id', ASCENDING), ('url', ASCENDING)], 'name': 'idx_url_task_url'},
            ],
            'user': [
                {'keys': [('username', ASCENDING)], 'name': 'idx_user_username', 'unique': True},
                {'keys': [('token', ASCENDING)], 'name': 'idx_user_token'},
                {'keys': [('api_key', ASCENDING)], 'name': 'idx_user_api_key'},
            ],
            'audit_log': [
                {'keys': [('user', ASCENDING)], 'name': 'idx_audit_user'},
                {'keys': [('action', ASCENDING)], 'name': 'idx_audit_action'},
                {'keys': [('resource_type', ASCENDING), ('resource_id', ASCENDING)], 'name': 'idx_audit_resource'},
                {'keys': [('timestamp', DESCENDING)], 'name': 'idx_audit_timestamp'},
                {'keys': [('timestamp', DESCENDING)], 'name': 'idx_audit_ttl', 'expireAfterSeconds': 7776000},  # 90天TTL
            ],
        }

        for collection_name, indexes in index_config.items():
            collection = cls._db[collection_name]
            for index_info in indexes:
                try:
                    keys = index_info['keys']
                    name = index_info.get('name')
                    unique = index_info.get('unique', False)

                    collection.create_index(
                        keys,
                        name=name,
                        unique=unique,
                        background=True  # 后台创建不阻塞
                    )
                except Exception as e:
                    logger.warning(f"Failed to create index on {collection_name}: {e}")

    @classmethod
    def get_collection(cls, collection_name: str, db_name: Optional[str] = None) -> Collection:
        """
        获取数据库集合

        Args:
            collection_name: 集合名称
            db_name: 数据库名称（可选，默认使用初始化的数据库）

        Returns:
            MongoDB集合对象

        Raises:
            RuntimeError: 数据库未初始化时抛出异常
        """
        if cls._db is None:
            raise RuntimeError("DatabaseManager not initialized. Call init() first.")

        if db_name:
            return cls._client[db_name][collection_name]
        return cls._db[collection_name]

    @classmethod
    def safe_find_one(cls, collection_name: str, query: Dict[str, Any]) -> Optional[Dict]:
        """
        安全的 find_one 查询（自动清理 NoSQL 注入）

        Args:
            collection_name: 集合名称
            query: 查询条件

        Returns:
            查询结果，未找到返回 None
        """
        collection = cls.get_collection(collection_name)
        return MongoSanitizer.safe_find_one(collection, query)

    @classmethod
    def safe_find(cls, collection_name: str, query: Dict[str, Any]) -> List[Dict]:
        """
        安全的 find 查询（自动清理 NoSQL 注入）

        Args:
            collection_name: 集合名称
            query: 查询条件

        Returns:
            查询结果列表
        """
        collection = cls.get_collection(collection_name)
        return MongoSanitizer.safe_find(collection, query)

    @classmethod
    def safe_insert_one(cls, collection_name: str, document: Dict[str, Any]) -> bool:
        """
        安全的 insert_one 操作（自动清理 NoSQL 注入）

        Args:
            collection_name: 集合名称
            document: 要插入的文档

        Returns:
            是否插入成功
        """
        collection = cls.get_collection(collection_name)
        return MongoSanitizer.safe_insert_one(collection, document)

    @classmethod
    def safe_update_one(cls, collection_name: str, filter_query: Dict, update: Dict) -> bool:
        """
        安全的 update_one 操作（自动清理 NoSQL 注入）

        Args:
            collection_name: 集合名称
            filter_query: 过滤条件
            update: 更新内容

        Returns:
            是否更新成功
        """
        collection = cls.get_collection(collection_name)
        return MongoSanitizer.safe_update_one(collection, filter_query, update)

    @classmethod
    def safe_delete_one(cls, collection_name: str, query: Dict[str, Any]) -> bool:
        """
        安全的 delete_one 操作（自动清理 NoSQL 注入）

        Args:
            collection_name: 集合名称
            query: 删除条件

        Returns:
            是否删除成功
        """
        collection = cls.get_collection(collection_name)
        return MongoSanitizer.safe_delete_one(collection, query)

    @classmethod
    def get_db(cls, db_name: Optional[str] = None) -> Database:
        """
        获取数据库实例

        Args:
            db_name: 数据库名称（可选）

        Returns:
            MongoDB数据库对象

        Raises:
            RuntimeError: 数据库未初始化时抛出异常
        """
        if cls._db is None:
            raise RuntimeError("DatabaseManager not initialized. Call init() first.")

        if db_name:
            return cls._client[db_name]
        return cls._db

    @classmethod
    def get_client(cls) -> MongoClient:
        """
        获取MongoDB客户端实例

        Returns:
            MongoClient对象

        Raises:
            RuntimeError: 数据库未初始化时抛出异常
        """
        if cls._client is None:
            raise RuntimeError("DatabaseManager not initialized. Call init() first.")
        return cls._client

    @classmethod
    def close(cls) -> None:
        """关闭数据库连接"""
        if cls._client:
            cls._client.close()
            cls._client = None
            cls._db = None
            cls._instance = None
            logger.info("Database connection closed")

    @classmethod
    def is_initialized(cls) -> bool:
        """检查数据库是否已初始化"""
        return cls._client is not None


# 便捷函数（保持向后兼容）
def get_collection(collection: str, db_name: Optional[str] = None) -> Collection:
    """获取数据库集合（便捷函数）"""
    return DatabaseManager.get_collection(collection, db_name)


def get_db(db_name: Optional[str] = None) -> Database:
    """获取数据库实例（便捷函数）"""
    return DatabaseManager.get_db(db_name)


def init_db(mongo_url: Optional[str] = None, db_name: Optional[str] = None) -> None:
    """初始化数据库（便捷函数）"""
    DatabaseManager.init(mongo_url, db_name)
