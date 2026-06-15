# -*- coding: utf-8 -*-
"""
ARL IP服务
封装IP侦察相关业务逻辑
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.exceptions import NotFoundException, ValidationException
from app.core.validators import validate_ip, validate_ip_range
from app.core.audit import audit_log
from app.database.repositories import IPRepository, TaskRepository

logger = logging.getLogger(__name__)


class IPService:
    """
    IP服务

    封装IP侦察的业务逻辑，包括：
    - IP信息查询
    - 地理位置查询
    - ASN信息查询
    - 端口信息查询

    用法：
        service = IPService()
        ip_info = service.get_ip_info('8.8.8.8')
    """

    def __init__(self):
        self.repo = IPRepository()
        self.task_repo = TaskRepository()

    def get_ip_info(self, ip: str) -> Dict[str, Any]:
        """
        获取IP信息

        Args:
            ip: IP地址

        Returns:
            IP信息字典

        Raises:
            ValidationException: IP格式无效
            NotFoundException: IP不存在
        """
        # 验证IP格式
        validate_ip(ip)

        # 查询IP
        ip_info = self.repo.find_by_ip(ip)
        if not ip_info:
            raise NotFoundException(f"IP not found: {ip}", resource_type='ip')

        return ip_info

    def find_by_task(self, task_id: str) -> List[Dict[str, Any]]:
        """
        根据任务ID查找IP

        Args:
            task_id: 任务ID

        Returns:
            IP列表
        """
        # 验证任务存在
        task = self.task_repo.find_by_task_id(task_id)
        if not task:
            raise NotFoundException(f"Task not found: {task_id}", resource_type='task')

        return self.repo.find_by_task(task_id)

    def find_by_asn(self, asn: str) -> List[Dict[str, Any]]:
        """
        根据ASN查找IP

        Args:
            asn: ASN编号

        Returns:
            IP列表
        """
        return self.repo.find_by_asn(asn)

    def find_by_country(self, country_code: str) -> List[Dict[str, Any]]:
        """
        根据国家代码查找IP

        Args:
            country_code: 国家代码（如CN、US）

        Returns:
            IP列表
        """
        return self.repo.find_by_geo(country_code.upper())

    @audit_log(action='create', resource='ip')
    def add_ip(
        self,
        ip: str,
        task_id: Optional[str] = None,
        geoip: Optional[Dict] = None,
        asn: Optional[Dict] = None,
        ports: Optional[List[int]] = None,
        os: Optional[str] = None
    ) -> str:
        """
        添加IP记录

        Args:
            ip: IP地址
            task_id: 关联任务ID
            geoip: 地理位置信息
            asn: ASN信息
            ports: 开放端口列表
            os: 操作系统指纹

        Returns:
            IP记录ID

        Raises:
            ValidationException: IP格式无效
        """
        # 验证IP格式
        validate_ip(ip)

        ip_doc = {
            'ip': ip,
            'task_id': task_id,
            'geoip': geoip,
            'asn': asn,
            'ports': ports or [],
            'os': os,
            'created_at': datetime.now()
        }

        ip_id = self.repo.insert_one(ip_doc)
        logger.info(f"IP added: {ip}")

        return ip_id

    def bulk_add_ips(self, ips: List[Dict[str, Any]]) -> int:
        """
        批量添加IP

        Args:
            ips: IP列表

        Returns:
            添加数量
        """
        # 验证所有IP
        for ip in ips:
            validate_ip(ip.get('ip', ''))

        operations = []
        for ip in ips:
            operations.append({
                'updateOne': {
                    'filter': {'ip': ip['ip']},
                    'update': {'$set': ip},
                    'upsert': True
                }
            })

        try:
            result = self.repo.bulk_write(operations)
            return result['upserted_count'] + result['modified_count']
        except Exception as e:
            logger.error(f"Failed to bulk add IPs: {e}")
            return 0

    def search_ips(
        self,
        query: str,
        country_code: Optional[str] = None,
        asn: Optional[str] = None,
        limit: int = 100,
        skip: int = 0
    ) -> List[Dict[str, Any]]:
        """
        搜索IP

        Args:
            query: 搜索关键词（支持IP或CIDR）
            country_code: 按国家代码过滤
            asn: 按ASN过滤
            limit: 返回数量限制
            skip: 跳过数量

        Returns:
            IP列表
        """
        filter_query = {}

        # 支持IP或CIDR搜索
        if '/' in query:
            validate_ip_range(query)
            # CIDR搜索
            from app.utils.ip import transfer_ip_scope
            cidr = transfer_ip_scope(query)
            filter_query['ip'] = {'$regex': f"^{cidr.split('/')[0]}"}
        else:
            filter_query['ip'] = {'$regex': query, '$options': 'i'}

        if country_code:
            filter_query['geoip.country_code'] = country_code.upper()

        if asn:
            filter_query['asn.number'] = asn

        return self.repo.find_many(
            filter_query,
            sort=[('created_at', -1)],
            limit=limit,
            skip=skip
        )

    def count_ips(
        self,
        country_code: Optional[str] = None,
        asn: Optional[str] = None,
        task_id: Optional[str] = None
    ) -> int:
        """
        统计IP数量

        Args:
            country_code: 按国家代码过滤
            asn: 按ASN过滤
            task_id: 按任务ID过滤

        Returns:
            IP数量
        """
        filter_query = {}

        if country_code:
            filter_query['geoip.country_code'] = country_code.upper()
        if asn:
            filter_query['asn.number'] = asn
        if task_id:
            filter_query['task_id'] = task_id

        return self.repo.count(filter_query)

    def delete_ip(self, ip: str) -> bool:
        """
        删除IP记录

        Args:
            ip: IP地址

        Returns:
            是否删除成功
        """
        ip_info = self.get_ip_info(ip)
        return self.repo.delete_by_id(str(ip_info['_id']))

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取IP统计信息

        Returns:
            统计信息字典
        """
        pipeline = [
            {
                '$group': {
                    '_id': '$geoip.country_code',
                    'count': {'$sum': 1}
                }
            },
            {'$sort': {'count': -1}},
            {'$limit': 10}
        ]

        try:
            result = self.repo.aggregate(pipeline)
            return {
                'total': self.repo.count({}),
                'top_countries': {item['_id']: item['count'] for item in result if item['_id']}
            }
        except Exception as e:
            logger.error(f"Failed to get IP statistics: {e}")
            return {'total': 0, 'top_countries': {}}
