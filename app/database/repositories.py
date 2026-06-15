# -*- coding: utf-8 -*-
"""
ARL数据访问层（Repository模式）
提供统一的数据库访问接口，封装MongoDB操作
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, TypeVar, Generic

from bson import ObjectId
from bson.errors import InvalidId
from pymongo.collection import Collection
from pymongo.results import DeleteResult, UpdateResult

from app.core.exceptions import DatabaseException, NotFoundException, ValidationException
from app.core.types import TaskInfo, DomainInfo, IPInfo, SiteInfo, UserInfo, TaskStatus
from app.utils.sanitizer import MongoSanitizer

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BaseRepository(Generic[T]):
    """
    基础Repository类

    提供通用的CRUD操作，所有实体Repository都应继承此类

    用法：
        class TaskRepository(BaseRepository[TaskInfo]):
            collection_name = 'task'
            model_class = TaskInfo
    """

    collection_name: str = ''
    model_class: Any = None

    def __init__(self):
        if not self.collection_name:
            raise ValueError("collection_name must be set")

    @property
    def collection(self) -> Collection:
        """获取MongoDB集合"""
        from app.database.connection import get_collection
        return get_collection(self.collection_name)

    def find_by_id(self, id: str) -> Optional[Dict[str, Any]]:
        """
        根据ID查找文档

        Args:
            id: 文档ID

        Returns:
            文档字典，未找到返回None

        Raises:
            ValidationException: ID格式无效
        """
        try:
            oid = ObjectId(id)
            return self.find_one({'_id': oid})
        except InvalidId:
            raise ValidationException(f"Invalid ID format: {id}", field='id')
        except Exception as e:
            raise DatabaseException(f"Failed to find document by ID: {e}")

    def find_one(self, filter: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        查找单个文档（自动清理 NoSQL 注入）

        Args:
            filter: 查询条件

        Returns:
            文档字典，未找到返回None
        """
        try:
            clean_filter = MongoSanitizer.sanitize_query(filter)
            return self.collection.find_one(clean_filter)
        except Exception as e:
            raise DatabaseException(f"Failed to find document: {e}")

    def find_many(
        self,
        filter: Dict[str, Any],
        sort: Optional[List[tuple]] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        查找多个文档（自动清理 NoSQL 注入）

        Args:
            filter: 查询条件
            sort: 排序规则
            limit: 返回数量限制
            skip: 跳过数量

        Returns:
            文档列表
        """
        try:
            clean_filter = MongoSanitizer.sanitize_query(filter)
            cursor = self.collection.find(clean_filter)
            if sort:
                cursor = cursor.sort(sort)
            cursor = cursor.skip(skip).limit(limit)
            return list(cursor)
        except Exception as e:
            raise DatabaseException(f"Failed to find documents: {e}")

    def count(self, filter: Dict[str, Any] = None) -> int:
        """
        统计文档数量（自动清理 NoSQL 注入）

        Args:
            filter: 查询条件

        Returns:
            文档数量
        """
        try:
            clean_filter = MongoSanitizer.sanitize_query(filter or {})
            return self.collection.count_documents(clean_filter)
        except Exception as e:
            raise DatabaseException(f"Failed to count documents: {e}")

    def insert_one(self, document: Dict[str, Any]) -> str:
        """
        插入单个文档（自动清理 NoSQL 注入）

        Args:
            document: 文档字典

        Returns:
            插入文档的ID
        """
        try:
            clean_doc = MongoSanitizer.sanitize_value(document)
            result = self.collection.insert_one(clean_doc)
            return str(result.inserted_id)
        except Exception as e:
            raise DatabaseException(f"Failed to insert document: {e}")

    def insert_many(self, documents: List[Dict[str, Any]]) -> List[str]:
        """
        批量插入文档（自动清理 NoSQL 注入）

        Args:
            documents: 文档列表

        Returns:
            插入文档的ID列表
        """
        try:
            clean_docs = [MongoSanitizer.sanitize_value(doc) for doc in documents]
            result = self.collection.insert_many(clean_docs)
            return [str(id) for id in result.inserted_ids]
        except Exception as e:
            raise DatabaseException(f"Failed to insert documents: {e}")

    def update_one(
        self,
        filter: Dict[str, Any],
        update: Dict[str, Any],
        upsert: bool = False
    ) -> bool:
        """
        更新单个文档（自动清理 NoSQL 注入）

        Args:
            filter: 查询条件
            update: 更新内容
            upsert: 不存在时是否插入

        Returns:
            是否修改成功
        """
        try:
            clean_filter = MongoSanitizer.sanitize_query(filter)
            clean_update = MongoSanitizer.sanitize_value(update)
            result = self.collection.update_one(clean_filter, clean_update, upsert=upsert)
            return result.modified_count > 0
        except Exception as e:
            raise DatabaseException(f"Failed to update document: {e}")

    def update_by_id(self, id: str, update: Dict[str, Any]) -> bool:
        """
        根据ID更新文档

        Args:
            id: 文档ID
            update: 更新内容

        Returns:
            是否修改成功
        """
        try:
            oid = ObjectId(id)
            return self.update_one({'_id': oid}, update)
        except InvalidId:
            raise ValidationException(f"Invalid ID format: {id}", field='id')

    def delete_one(self, filter: Dict[str, Any]) -> bool:
        """
        删除单个文档（自动清理 NoSQL 注入）

        Args:
            filter: 查询条件

        Returns:
            是否删除成功
        """
        try:
            clean_filter = MongoSanitizer.sanitize_query(filter)
            result = self.collection.delete_one(clean_filter)
            return result.deleted_count > 0
        except Exception as e:
            raise DatabaseException(f"Failed to delete document: {e}")

    def delete_by_id(self, id: str) -> bool:
        """
        根据ID删除文档

        Args:
            id: 文档ID

        Returns:
            是否删除成功
        """
        try:
            oid = ObjectId(id)
            return self.delete_one({'_id': oid})
        except InvalidId:
            raise ValidationException(f"Invalid ID format: {id}", field='id')

    def delete_many(self, filter: Dict[str, Any]) -> int:
        """
        批量删除文档（自动清理 NoSQL 注入）

        Args:
            filter: 查询条件

        Returns:
            删除数量
        """
        try:
            clean_filter = MongoSanitizer.sanitize_query(filter)
            result = self.collection.delete_many(clean_filter)
            return result.deleted_count
        except Exception as e:
            raise DatabaseException(f"Failed to delete documents: {e}")

    def exists(self, filter: Dict[str, Any]) -> bool:
        """
        检查文档是否存在（自动清理 NoSQL 注入）

        Args:
            filter: 查询条件

        Returns:
            是否存在
        """
        try:
            clean_filter = MongoSanitizer.sanitize_query(filter)
            count = self.collection.count_documents(clean_filter, limit=1)
            return count > 0
        except Exception as e:
            raise DatabaseException(f"Failed to check existence: {e}")

    def find_by_task(self, task_id: str) -> List[Dict[str, Any]]:
        """
        根据任务ID查找文档（通用方法）

        Args:
            task_id: 任务ID

        Returns:
            文档列表
        """
        return self.find_many({'task_id': task_id})

    def aggregate(self, pipeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        执行聚合管道（自动清理 NoSQL 注入）

        Args:
            pipeline: 聚合管道

        Returns:
            聚合结果列表
        """
        try:
            clean_pipeline = [MongoSanitizer.sanitize_value(stage) for stage in pipeline]
            return list(self.collection.aggregate(clean_pipeline))
        except Exception as e:
            raise DatabaseException(f"Failed to execute aggregation: {e}")

    def bulk_write(self, operations: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        批量写入操作（自动清理 NoSQL 注入）

        Args:
            operations: 操作列表

        Returns:
            操作结果统计
        """
        try:
            clean_ops = [MongoSanitizer.sanitize_value(op) for op in operations]
            result = self.collection.bulk_write(clean_ops)
            return {
                'inserted_count': result.inserted_count,
                'modified_count': result.modified_count,
                'upserted_count': result.upserted_count,
                'deleted_count': result.deleted_count
            }
        except Exception as e:
            raise DatabaseException(f"Failed to bulk write: {e}")

    def bulk_upsert(self, documents: List[Dict[str, Any]], filter_field: str) -> int:
        """
        批量更新插入（通用方法）

        Args:
            documents: 文档列表
            filter_field: 用于匹配的字段名

        Returns:
            操作数量
        """
        if not documents:
            return 0

        operations = []
        for doc in documents:
            if filter_field in doc:
                operations.append({
                    'updateOne': {
                        'filter': {filter_field: doc[filter_field]},
                        'update': {'$set': doc},
                        'upsert': True
                    }
                })

        if not operations:
            return 0

        try:
            clean_ops = [MongoSanitizer.sanitize_value(op) for op in operations]
            result = self.collection.bulk_write(clean_ops)
            return result.upserted_count + result.modified_count
        except Exception as e:
            raise DatabaseException(f"Failed to bulk upsert: {e}")

    def get_statistics(self, group_field: str = '$status') -> Dict[str, Any]:
        """
        获取通用统计信息

        Args:
            group_field: 分组字段

        Returns:
            统计信息字典
        """
        pipeline = [
            {'$group': {'_id': group_field, 'count': {'$sum': 1}}}
        ]
        try:
            result = self.aggregate(pipeline)
            stats = {}
            for item in result:
                key = item['_id'] if item['_id'] is not None else 'unknown'
                stats[key] = item['count']
            stats['total'] = sum(stats.values())
            return stats
        except Exception as e:
            raise DatabaseException(f"Failed to get statistics: {e}")


class TaskRepository(BaseRepository[TaskInfo]):
    """任务数据访问"""

    collection_name = 'task'

    def find_by_task_id(self, task_id: str) -> Optional[Dict[str, Any]]:
        """根据任务ID查找"""
        return self.find_one({'task_id': task_id})

    def find_by_status(self, status: TaskStatus, limit: int = 100) -> List[Dict[str, Any]]:
        """根据状态查找任务"""
        return self.find_many({'status': status.value}, limit=limit)

    def find_by_target(self, target: str) -> List[Dict[str, Any]]:
        """根据目标查找任务"""
        return self.find_many({'target': target})

    def find_by_user(self, username: str, limit: int = 100) -> List[Dict[str, Any]]:
        """根据用户查找任务"""
        return self.find_many({'created_by': username}, limit=limit)

    def update_status(self, task_id: str, status: TaskStatus, error_message: Optional[str] = None) -> bool:
        """更新任务状态"""
        update = {
            '$set': {
                'status': status.value,
                'updated_at': datetime.now()
            }
        }
        if status == TaskStatus.COMPLETED:
            update['$set']['completed_at'] = datetime.now()
        if error_message:
            update['$set']['error_message'] = error_message

        return self.update_one({'task_id': task_id}, update)

    def get_statistics(self) -> Dict[str, Any]:
        """获取任务统计"""
        pipeline = [
            {'$group': {'_id': '$status', 'count': {'$sum': 1}}}
        ]
        try:
            result = list(self.collection.aggregate(pipeline))
            stats = {item['_id']: item['count'] for item in result}
            stats['total'] = sum(stats.values())
            return stats
        except Exception as e:
            raise DatabaseException(f"Failed to get statistics: {e}")


class DomainRepository(BaseRepository[DomainInfo]):
    """域名数据访问"""

    collection_name = 'domain'

    def find_by_domain(self, domain: str) -> Optional[Dict[str, Any]]:
        """根据域名查找"""
        return self.find_one({'domain': domain})

    def find_by_ip(self, ip: str) -> List[Dict[str, Any]]:
        """根据IP查找域名"""
        return self.find_many({'ip': ip})

    def find_by_task(self, task_id: str) -> List[Dict[str, Any]]:
        """根据任务ID查找域名"""
        return self.find_many({'task_id': task_id})

    def find_subdomains(self, parent_domain: str) -> List[Dict[str, Any]]:
        """查找子域名"""
        import re
        regex = f"^{re.escape(parent_domain)}$|\\.{re.escape(parent_domain)}$"
        return self.find_many({'domain': {'$regex': regex}})

    def bulk_upsert(self, domains: List[Dict[str, Any]]) -> int:
        """批量更新插入"""
        if not domains:
            return 0

        operations = []
        for domain in domains:
            operations.append({
                'updateOne': {
                    'filter': {'domain': domain['domain']},
                    'update': {'$set': domain},
                    'upsert': True
                }
            })

        try:
            result = self.collection.bulk_write(operations)
            return result.upserted_count + result.modified_count
        except Exception as e:
            raise DatabaseException(f"Failed to bulk upsert domains: {e}")


class IPRepository(BaseRepository[IPInfo]):
    """IP数据访问"""

    collection_name = 'ip'

    def find_by_ip(self, ip: str) -> Optional[Dict[str, Any]]:
        """根据IP查找"""
        return self.find_one({'ip': ip})

    def find_by_task(self, task_id: str) -> List[Dict[str, Any]]:
        """根据任务ID查找"""
        return self.find_many({'task_id': task_id})

    def find_by_asn(self, asn: str) -> List[Dict[str, Any]]:
        """根据ASN查找"""
        return self.find_many({'asn.number': asn})

    def find_by_geo(self, country_code: str) -> List[Dict[str, Any]]:
        """根据国家代码查找"""
        return self.find_many({'geoip.country_code': country_code})


class SiteRepository(BaseRepository[SiteInfo]):
    """站点数据访问"""

    collection_name = 'site'

    def find_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """根据URL查找"""
        return self.find_one({'url': url})

    def find_by_task(self, task_id: str) -> List[Dict[str, Any]]:
        """根据任务ID查找"""
        return self.find_many({'task_id': task_id})

    def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        """根据状态查找"""
        return self.find_many({'status': status})

    def find_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """根据域名查找站点"""
        import re
        regex = f"^https?://([a-zA-Z0-9-]+\\.)*{re.escape(domain)}"
        return self.find_many({'url': {'$regex': regex}})


class UserRepository(BaseRepository[UserInfo]):
    """用户数据访问"""

    collection_name = 'user'

    def find_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """根据用户名查找"""
        return self.find_one({'username': username})

    def find_by_api_key(self, api_key: str) -> Optional[Dict[str, Any]]:
        """根据API Key查找"""
        return self.find_one({'api_key': api_key})

    def find_by_token(self, token: str) -> Optional[Dict[str, Any]]:
        """根据Token查找"""
        return self.find_one({'token': token})

    def find_active_users(self) -> List[Dict[str, Any]]:
        """查找所有活跃用户"""
        return self.find_many({'is_active': True})

    def update_last_login(self, username: str) -> bool:
        """更新最后登录时间"""
        return self.update_one(
            {'username': username},
            {'$set': {'last_login': datetime.now()}}
        )

    def deactivate_user(self, username: str) -> bool:
        """停用用户"""
        return self.update_one(
            {'username': username},
            {'$set': {'is_active': False}}
        )


class URLRepository(BaseRepository):
    """URL数据访问"""

    collection_name = 'url'

    def find_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """根据URL查找"""
        return self.find_one({'url': url})

    def find_by_task(self, task_id: str) -> List[Dict[str, Any]]:
        """根据任务ID查找"""
        return self.find_many({'task_id': task_id})

    def find_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """根据域名查找"""
        import re
        regex = f"^https?://([a-zA-Z0-9-]+\\.)*{re.escape(domain)}"
        return self.find_many({'url': {'$regex': regex}})


class CertRepository(BaseRepository):
    """证书数据访问"""

    collection_name = 'cert'

    def find_by_serial(self, serial_number: str) -> Optional[Dict[str, Any]]:
        """根据序列号查找"""
        return self.find_one({'serial_number': serial_number})

    def find_by_task(self, task_id: str) -> List[Dict[str, Any]]:
        """根据任务ID查找"""
        return self.find_many({'task_id': task_id})

    def find_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """根据域名查找"""
        return self.find_many({'domain': domain})


class SchedulerRepository(BaseRepository):
    """调度器数据访问"""

    collection_name = 'scheduler'

    def find_by_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """根据任务ID查找"""
        return self.find_one({'task_id': task_id})

    def find_active(self) -> List[Dict[str, Any]]:
        """查找活跃的调度任务"""
        return self.find_many({'status': 'active'})

    def find_due_tasks(self) -> List[Dict[str, Any]]:
        """查找到期的调度任务"""
        return self.find_many({
            'status': 'active',
            'next_run': {'$lte': datetime.now()}
        })


# 导出所有Repository
__all__ = [
    'BaseRepository',
    'TaskRepository',
    'DomainRepository',
    'IPRepository',
    'SiteRepository',
    'UserRepository',
    'URLRepository',
    'CertRepository',
    'SchedulerRepository'
]
