# -*- coding: utf-8 -*-
"""
ARL域名服务
封装域名侦察相关业务逻辑
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.exceptions import NotFoundException, ValidationException
from app.core.validators import validate_domain
from app.core.audit import audit_log
from app.database.repositories import DomainRepository, TaskRepository

logger = logging.getLogger(__name__)


class DomainService:
    """
    域名服务

    封装域名侦察的业务逻辑，包括：
    - 域名查询
    - 子域名查找
    - WHOIS信息查询
    - DNS记录查询

    用法：
        service = DomainService()
        domains = service.find_subdomains('example.com')
    """

    def __init__(self):
        self.repo = DomainRepository()
        self.task_repo = TaskRepository()

    def get_domain_info(self, domain: str) -> Dict[str, Any]:
        """
        获取域名信息

        Args:
            domain: 域名

        Returns:
            域名信息字典

        Raises:
            ValidationException: 域名格式无效
            NotFoundException: 域名不存在
        """
        # 验证域名格式
        validate_domain(domain)

        # 查询域名
        domain_info = self.repo.find_by_domain(domain.lower())
        if not domain_info:
            raise NotFoundException(f"Domain not found: {domain}", resource_type='domain')

        return domain_info

    def find_by_ip(self, ip: str) -> List[Dict[str, Any]]:
        """
        根据IP查找关联域名

        Args:
            ip: IP地址

        Returns:
            域名列表
        """
        return self.repo.find_by_ip(ip)

    def find_by_task(self, task_id: str) -> List[Dict[str, Any]]:
        """
        根据任务ID查找域名

        Args:
            task_id: 任务ID

        Returns:
            域名列表
        """
        # 验证任务存在
        task = self.task_repo.find_by_task_id(task_id)
        if not task:
            raise NotFoundException(f"Task not found: {task_id}", resource_type='task')

        return self.repo.find_by_task(task_id)

    def find_subdomains(self, parent_domain: str) -> List[Dict[str, Any]]:
        """
        查找子域名

        Args:
            parent_domain: 父域名

        Returns:
            子域名列表
        """
        # 验证域名格式
        validate_domain(parent_domain)

        return self.repo.find_subdomains(parent_domain.lower())

    @audit_log(action='create', resource='domain')
    def add_domain(
        self,
        domain: str,
        ip: List[str],
        task_id: Optional[str] = None,
        whois: Optional[Dict] = None,
        dns_records: Optional[Dict] = None
    ) -> str:
        """
        添加域名记录

        Args:
            domain: 域名
            ip: IP列表
            task_id: 关联任务ID
            whois: WHOIS信息
            dns_records: DNS记录

        Returns:
            域名记录ID

        Raises:
            ValidationException: 域名格式无效
        """
        # 验证域名格式
        validate_domain(domain)

        domain_doc = {
            'domain': domain.lower(),
            'ip': ip,
            'task_id': task_id,
            'whois': whois,
            'dns_records': dns_records,
            'created_at': datetime.now()
        }

        domain_id = self.repo.insert_one(domain_doc)
        logger.info(f"Domain added: {domain}")

        return domain_id

    def bulk_add_domains(self, domains: List[Dict[str, Any]]) -> int:
        """
        批量添加域名

        Args:
            domains: 域名列表

        Returns:
            添加数量
        """
        # 验证所有域名
        for domain in domains:
            validate_domain(domain.get('domain', ''))

        return self.repo.bulk_upsert(domains)

    def search_domains(
        self,
        query: str,
        ip: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        搜索域名

        Args:
            query: 搜索关键词
            ip: 按IP过滤
            limit: 返回数量限制
            skip: 跳过数量

        Returns:
            域名列表
        """
        # 构建查询条件
        filter_query = {
            'domain': {'$regex': query, '$options': 'i'}
        }

        if ip:
            filter_query['ip'] = ip

        return self.repo.find_many(
            filter_query,
            sort=[('created_at', -1)],
            limit=limit,
            skip=skip
        )

    def count_domains(
        self,
        ip: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> int:
        """
        统计域名数量

        Args:
            ip: 按IP过滤
            task_id: 按任务ID过滤

        Returns:
            域名数量
        """
        filter_query = {}

        if ip:
            filter_query['ip'] = ip
        if task_id:
            filter_query['task_id'] = task_id

        return self.repo.count(filter_query)

    def delete_domain(self, domain: str) -> bool:
        """
        删除域名记录

        Args:
            domain: 域名

        Returns:
            是否删除成功
        """
        domain_info = self.get_domain_info(domain)
        return self.repo.delete_by_id(str(domain_info['_id']))

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取域名统计信息

        Returns:
            统计信息字典
        """
        pipeline = [
            {'$group': {'_id': None, 'total': {'$sum': 1}, 'unique_ips': {'$addToSet': '$ip'}}}
        ]

        try:
            result = self.repo.aggregate(pipeline)
            if result:
                stats = result[0]
                stats['unique_ip_count'] = len(stats.get('unique_ips', []))
                del stats['unique_ips']
                return stats
            return {'total': 0, 'unique_ip_count': 0}
        except Exception as e:
            logger.error(f"Failed to get domain statistics: {e}")
            return {'total': 0, 'unique_ip_count': 0}
