# -*- coding: utf-8 -*-
"""
ARL审计日志模块
记录关键操作，满足合规性要求
"""

import functools
import logging
import time
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from flask import request, g

from app.database.connection import get_collection
from app.core.types import UserInfo

logger = logging.getLogger(__name__)


class AuditLog:
    """
    审计日志记录器

    记录所有关键操作，包括：
    - 用户认证（登录/登出）
    - 数据访问（查询/导出）
    - 数据修改（创建/更新/删除）
    - 系统配置变更
    - 安全事件（认证失败/权限拒绝）

    用法：
        audit_log = AuditLog()
        audit_log.record(action='login', resource='user', details={'username': 'admin'})
    """

    COLLECTION_NAME = 'audit_log'

    def __init__(self):
        self._collection = None

    @property
    def collection(self):
        """获取审计日志集合"""
        if self._collection is None:
            self._collection = get_collection(self.COLLECTION_NAME)
        return self._collection

    def record(
        self,
        action: str,
        resource: str,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        user: Optional[str] = None,
        ip: Optional[str] = None,
        status: str = "success"
    ) -> None:
        """
        记录审计日志

        Args:
            action: 操作类型（如login, create_task, export_data）
            resource: 资源类型（如user, task, domain）
            resource_id: 资源ID
            details: 操作详情
            user: 操作用户（默认从g.current_user获取）
            ip: 客户端IP（默认从request获取）
            status: 操作状态（success/failure）
        """
        # 获取当前用户
        if user is None:
            current_user = getattr(g, 'current_user', None)
            user = current_user.get('username', 'anonymous') if current_user else 'anonymous'

        # 获取客户端IP
        if ip is None:
            ip = request.remote_addr if request else 'unknown'

        # 构建日志记录
        log_entry = {
            'timestamp': datetime.now(),
            'user': user,
            'action': action,
            'resource': resource,
            'resource_id': resource_id,
            'ip': ip,
            'status': status,
            'details': details or {},
            'user_agent': request.headers.get('User-Agent', '') if request else ''
        }

        try:
            self.collection.insert_one(log_entry)
            logger.debug(f"Audit log recorded: {action} on {resource} by {user}")
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception(f"Error in {__name__}: {e}")
            # 审计日志写入失败不应影响业务操作
            logger.error(f"Failed to record audit log: {e}")

    def query(
        self,
        user: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        status: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        查询审计日志

        Args:
            user: 按用户过滤
            action: 按操作过滤
            resource: 按资源类型过滤
            start_time: 开始时间
            end_time: 结束时间
            status: 按状态过滤
            limit: 返回数量限制
            skip: 跳过数量

        Returns:
            审计日志列表
        """
        query = {}

        if user:
            query['user'] = user
        if action:
            query['action'] = action
        if resource:
            query['resource'] = resource
        if status:
            query['status'] = status
        if start_time or end_time:
            query['timestamp'] = {}
            if start_time:
                query['timestamp']['$gte'] = start_time
            if end_time:
                query['timestamp']['$lte'] = end_time

        try:
            cursor = self.collection.find(query).sort('timestamp', -1).skip(skip).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to query audit logs: {e}")
            return []

    def count(
        self,
        user: Optional[str] = None,
        action: Optional[str] = None,
        resource: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """
        统计审计日志数量

        Args:
            user: 按用户过滤
            action: 按操作过滤
            resource: 按资源类型过滤
            start_time: 开始时间
            end_time: 结束时间

        Returns:
            日志数量
        """
        query = {}

        if user:
            query['user'] = user
        if action:
            query['action'] = action
        if resource:
            query['resource'] = resource
        if start_time or end_time:
            query['timestamp'] = {}
            if start_time:
                query['timestamp']['$gte'] = start_time
            if end_time:
                query['timestamp']['$lte'] = end_time

        try:
            return self.collection.count_documents(query)
        except Exception as e:
            logger.error(f"Failed to count audit logs: {e}")
            return 0

    def get_user_actions(
        self,
        username: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取用户最近操作

        Args:
            username: 用户名
            limit: 返回数量限制

        Returns:
            操作历史列表
        """
        return self.query(user=username, limit=limit)

    def get_resource_history(
        self,
        resource: str,
        resource_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        获取资源操作历史

        Args:
            resource: 资源类型
            resource_id: 资源ID
            limit: 返回数量限制

        Returns:
            操作历史列表
        """
        try:
            cursor = self.collection.find({
                'resource': resource,
                'resource_id': resource_id
            }).sort('timestamp', -1).limit(limit)
            return list(cursor)
        except Exception as e:
            logger.error(f"Failed to get resource history: {e}")
            return []


def audit_log(
    action: str,
    resource: str,
    get_resource_id: Optional[Callable] = None,
    include_details: bool = False
) -> Callable:
    """
    审计日志装饰器

    自动记录函数调用作为审计日志

    用法：
        @audit_log(action='create', resource='task')
        def create_task(task_data):
            ...

        @audit_log(action='login', resource='user', get_resource_id=lambda r: r.get('username'))
        def login(username, password):
            ...

    Args:
        action: 操作类型
        resource: 资源类型
        get_resource_id: 从函数参数或返回值提取资源ID的函数
        include_details: 是否包含函数参数详情

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            status = "success"
            details = {}
            resource_id = None

            # 提取资源ID
            if get_resource_id:
                try:
                    resource_id = get_resource_id(*args, **kwargs)
                except Exception as e:
                    # Resource ID extraction failed - non-critical, continue without it
                    import logging
                    logging.getLogger(__name__).debug(f"Failed to extract resource ID: {e}")

            # 记录请求详情
            if include_details:
                # 过滤敏感字段
                safe_kwargs = {k: v for k, v in kwargs.items()
                               if k not in ('password', 'token', 'api_key', 'secret')}
                details['kwargs'] = safe_kwargs
                if args:
                    details['args_count'] = len(args)

            try:
                result = func(*args, **kwargs)

                # 如果返回值是dict，尝试提取resource_id
                if isinstance(result, dict) and '_id' in result and not resource_id:
                    resource_id = str(result['_id'])

                return result
            except Exception as e:
                import logging
                logging.getLogger(__name__).exception(f"Error in {__name__}: {e}")
                status = "failure"
                details['error'] = str(e)
                raise
            finally:
                # 记录审计日志
                try:
                    audit = AuditLog()
                    duration_ms = (time.time() - start_time) * 1000
                    details['duration_ms'] = round(duration_ms, 2)

                    audit.record(
                        action=action,
                        resource=resource,
                        resource_id=resource_id,
                        details=details,
                        status=status
                    )
                except Exception as e:
                    logger.error(f"Failed to record audit log: {e}")

        return wrapper
    return decorator


# 导出
__all__ = [
    'AuditLog',
    'audit_log'
]
