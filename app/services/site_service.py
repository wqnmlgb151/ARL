# -*- coding: utf-8 -*-
"""
ARL站点服务
封装站点侦察相关业务逻辑
"""

import logging
import hashlib
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from app.core.exceptions import NotFoundException, ValidationException
from app.core.validators import validate_url
from app.core.audit import audit_log
from app.database.repositories import SiteRepository, TaskRepository

logger = logging.getLogger(__name__)


class SiteStatus(Enum):
    """站点状态枚举"""
    UNKNOWN = "unknown"
    ACTIVE = "active"
    INACTIVE = "inactive"
    REDIRECT = "redirect"


class SiteService:
    """
    站点服务

    封装站点侦察的业务逻辑，包括：
    - 站点信息查询
    - 站点状态管理
    - 站点截图管理
    - 技术栈识别

    用法：
        service = SiteService()
        site_info = service.get_site_info('https://example.com')
    """

    def __init__(self):
        self.repo = SiteRepository()
        self.task_repo = TaskRepository()

    def get_site_info(self, url: str) -> Dict[str, Any]:
        """
        获取站点信息

        Args:
            url: 站点URL

        Returns:
            站点信息字典

        Raises:
            ValidationException: URL格式无效
            NotFoundException: 站点不存在
        """
        # 验证URL格式
        validate_url(url)

        # 查询站点
        site_info = self.repo.find_by_url(url)
        if not site_info:
            raise NotFoundException(f"Site not found: {url}", resource_type='site')

        return site_info

    def find_by_task(self, task_id: str) -> List[Dict[str, Any]]:
        """
        根据任务ID查找站点

        Args:
            task_id: 任务ID

        Returns:
            站点列表
        """
        # 验证任务存在
        task = self.task_repo.find_by_task_id(task_id)
        if not task:
            raise NotFoundException(f"Task not found: {task_id}", resource_type='task')

        return self.repo.find_by_task(task_id)

    def find_by_status(self, status: str) -> List[Dict[str, Any]]:
        """
        根据状态查找站点

        Args:
            status: 站点状态

        Returns:
            站点列表
        """
        return self.repo.find_by_status(status)

    def find_by_domain(self, domain: str) -> List[Dict[str, Any]]:
        """
        根据域名查找站点

        Args:
            domain: 域名

        Returns:
            站点列表
        """
        return self.repo.find_by_domain(domain)

    @audit_log(action='create', resource='site')
    def add_site(
        self,
        url: str,
        task_id: Optional[str] = None,
        status: SiteStatus = SiteStatus.UNKNOWN,
        title: Optional[str] = None,
        http_status: Optional[int] = None,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[bytes] = None,
        technologies: Optional[List[str]] = None,
        screenshot: Optional[str] = None
    ) -> str:
        """
        添加站点记录

        Args:
            url: 站点URL
            task_id: 关联任务ID
            status: 站点状态
            title: 页面标题
            http_status: HTTP状态码
            headers: HTTP响应头
            body: 响应体（用于计算哈希）
            technologies: 使用的技术栈
            screenshot: 截图路径

        Returns:
            站点记录ID

        Raises:
            ValidationException: URL格式无效
        """
        # 验证URL格式
        validate_url(url)

        # 计算响应体哈希
        body_hash = None
        if body:
            body_hash = hashlib.md5(body).hexdigest()

        site_doc = {
            'url': url,
            'task_id': task_id,
            'status': status.value if isinstance(status, SiteStatus) else status,
            'title': title,
            'http_status': http_status,
            'headers': headers or {},
            'body_hash': body_hash,
            'technologies': technologies or [],
            'screenshot': screenshot,
            'created_at': datetime.now()
        }

        site_id = self.repo.insert_one(site_doc)
        logger.info(f"Site added: {url}")

        return site_id

    def bulk_add_sites(self, sites: List[Dict[str, Any]]) -> int:
        """
        批量添加站点

        Args:
            sites: 站点列表

        Returns:
            添加数量
        """
        # 验证所有URL
        for site in sites:
            validate_url(site.get('url', ''))

        try:
            result = self.repo.insert_many(sites)
            return len(result)
        except Exception as e:
            logger.error(f"Failed to bulk add sites: {e}")
            return 0

    def search_sites(
        self,
        query: str,
        status: Optional[str] = None,
        domain: Optional[str] = None,
        technology: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        搜索站点

        Args:
            query: 搜索关键词
            status: 按状态过滤
            domain: 按域名过滤
            technology: 按技术栈过滤
            limit: 返回数量限制
            skip: 跳过数量

        Returns:
            站点列表
        """
        filter_query = {
            '$or': [
                {'url': {'$regex': query, '$options': 'i'}},
                {'title': {'$regex': query, '$options': 'i'}}
            ]
        }

        if status:
            filter_query['status'] = status

        if domain:
            import re
            regex = f"^https?://([a-zA-Z0-9-]+\\.)*{re.escape(domain)}"
            filter_query['url'] = {'$regex': regex}

        if technology:
            filter_query['technologies'] = {'$regex': technology, '$options': 'i'}

        return self.repo.find_many(
            filter_query,
            sort=[('created_at', -1)],
            limit=limit,
            skip=skip
        )

    def count_sites(
        self,
        status: Optional[str] = None,
        domain: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> int:
        """
        统计站点数量

        Args:
            status: 按状态过滤
            domain: 按域名过滤
            task_id: 按任务ID过滤

        Returns:
            站点数量
        """
        filter_query = {}

        if status:
            filter_query['status'] = status
        if domain:
            import re
            regex = f"^https?://([a-zA-Z0-9-]+\\.)*{re.escape(domain)}"
            filter_query['url'] = {'$regex': regex}
        if task_id:
            filter_query['task_id'] = task_id

        return self.repo.count(filter_query)

    def update_site_status(
        self,
        url: str,
        status: str,
        http_status: Optional[int] = None
    ) -> bool:
        """
        更新站点状态

        Args:
            url: 站点URL
            status: 新状态
            http_status: HTTP状态码

        Returns:
            是否更新成功
        """
        update = {
            '$set': {
                'status': status,
                'updated_at': datetime.now()
            }
        }

        if http_status:
            update['$set']['http_status'] = http_status

        return self.repo.update_one({'url': url}, update)

    def delete_site(self, url: str) -> bool:
        """
        删除站点记录

        Args:
            url: 站点URL

        Returns:
            是否删除成功
        """
        site_info = self.get_site_info(url)
        return self.repo.delete_by_id(str(site_info['_id']))

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取站点统计信息

        Returns:
            统计信息字典
        """
        pipeline = [
            {
                '$group': {
                    '_id': '$status',
                    'count': {'$sum': 1}
                }
            }
        ]

        try:
            result = self.repo.aggregate(pipeline)
            stats = {item['_id']: item['count'] for item in result}
            stats['total'] = sum(stats.values())
            return stats
        except Exception as e:
            logger.error(f"Failed to get site statistics: {e}")
            return {'total': 0}
