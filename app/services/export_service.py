# -*- coding: utf-8 -*-
"""
ARL导出服务
封装数据导出相关业务逻辑
"""

import csv
import json
import logging
import os
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

from bson import ObjectId

from app.config import Config
from app.core.exceptions import ValidationException
from app.core.audit import audit_log
from app.database.repositories import (
    DomainRepository,
    IPRepository,
    SiteRepository,
    URLRepository,
    CertRepository,
    TaskRepository
)

logger = logging.getLogger(__name__)

# 常量定义
EXPORT_FORMATS = ('json', 'csv')
DEFAULT_EXPORT_LIMIT = 10000


class ExportService:
    """
    导出服务

    封装数据导出的业务逻辑，支持多种格式：
    - JSON
    - CSV

    用法：
        service = ExportService()
        file_path = service.export_domains(task_id='xxx', format='json')
    """

    def __init__(self):
        # 懒加载Repository，按需创建
        self._domain_repo = None
        self._ip_repo = None
        self._site_repo = None
        self._url_repo = None
        self._cert_repo = None
        self._task_repo = None

        # 导出目录
        self.export_dir = os.path.join(Config.BASE_DIR, 'exports')
        os.makedirs(self.export_dir, exist_ok=True)

    @property
    def domain_repo(self) -> DomainRepository:
        if self._domain_repo is None:
            self._domain_repo = DomainRepository()
        return self._domain_repo

    @property
    def ip_repo(self) -> IPRepository:
        if self._ip_repo is None:
            self._ip_repo = IPRepository()
        return self._ip_repo

    @property
    def site_repo(self) -> SiteRepository:
        if self._site_repo is None:
            self._site_repo = SiteRepository()
        return self._site_repo

    @property
    def url_repo(self) -> URLRepository:
        if self._url_repo is None:
            self._url_repo = URLRepository()
        return self._url_repo

    @property
    def cert_repo(self) -> CertRepository:
        if self._cert_repo is None:
            self._cert_repo = CertRepository()
        return self._cert_repo

    @property
    def task_repo(self) -> TaskRepository:
        if self._task_repo is None:
            self._task_repo = TaskRepository()
        return self._task_repo

    def _generate_filename(self, prefix: str, format: str) -> str:
        """生成导出文件名"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        return f"{prefix}_{timestamp}.{format}"

    def _write_json(self, data: List[Dict], file_path: str) -> None:
        """写入JSON文件"""
        def json_serializer(obj):
            if isinstance(obj, datetime):
                return obj.isoformat()
            if isinstance(obj, ObjectId):
                return str(obj)
            if hasattr(obj, '__str__'):
                return str(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, default=json_serializer, indent=2)

    def _write_csv(self, data: List[Dict], file_path: str) -> None:
        """写入CSV文件"""
        if not data:
            return

        # 使用集合优化字段查找
        fields_set = set()
        for item in data:
            fields_set.update(item.keys())
        fields = list(fields_set)

        with open(file_path, 'w', encoding='utf-8-sig', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
            writer.writeheader()

            for item in data:
                row = {}
                for key, value in item.items():
                    if isinstance(value, (dict, list)):
                        row[key] = json.dumps(value, ensure_ascii=False, default=str)
                    elif isinstance(value, datetime):
                        row[key] = value.isoformat()
                    elif isinstance(value, ObjectId):
                        row[key] = str(value)
                    else:
                        row[key] = value
                writer.writerow(row)

    def _export_data(
        self,
        repo: Any,
        query_builder: Callable,
        resource_name: str,
        format: str,
        fields: Optional[List[str]] = None,
        limit: int = DEFAULT_EXPORT_LIMIT
    ) -> str:
        """
        通用导出方法

        Args:
            repo: Repository实例
            query_builder: 查询构建函数
            resource_name: 资源名称（用于文件名）
            format: 导出格式
            fields: 要导出的字段列表
            limit: 最大导出数量

        Returns:
            导出文件路径
        """
        if format not in EXPORT_FORMATS:
            raise ValidationException(f"Unsupported format: {format}", field='format')

        # 构建查询并执行
        query = query_builder()
        data = repo.find_many(query, limit=limit)

        # 过滤字段
        if fields:
            data = [{k: v for k, v in d.items() if k in fields} for d in data]

        # 生成文件路径
        filename = self._generate_filename(resource_name, format)
        file_path = os.path.join(self.export_dir, filename)

        # 写入文件
        if format == 'json':
            self._write_json(data, file_path)
        elif format == 'csv':
            self._write_csv(data, file_path)

        logger.info(f"{resource_name} exported: {len(data)} records to {file_path}")
        return file_path

    @audit_log(action='export', resource='domain')
    def export_domains(
        self,
        task_id: Optional[str] = None,
        ip: Optional[str] = None,
        format: str = 'json',
        fields: Optional[List[str]] = None
    ) -> str:
        """导出域名数据"""
        def query_builder():
            query = {}
            if task_id:
                query['task_id'] = task_id
            if ip:
                query['ip'] = ip
            return query

        return self._export_data(self.domain_repo, query_builder, 'domains', format, fields)

    @audit_log(action='export', resource='ip')
    def export_ips(
        self,
        task_id: Optional[str] = None,
        country_code: Optional[str] = None,
        format: str = 'json',
        fields: Optional[List[str]] = None
    ) -> str:
        """导出IP数据"""
        def query_builder():
            query = {}
            if task_id:
                query['task_id'] = task_id
            if country_code:
                query['geoip.country_code'] = country_code.upper()
            return query

        return self._export_data(self.ip_repo, query_builder, 'ips', format, fields)

    @audit_log(action='export', resource='site')
    def export_sites(
        self,
        task_id: Optional[str] = None,
        status: Optional[str] = None,
        format: str = 'json',
        fields: Optional[List[str]] = None
    ) -> str:
        """导出站点数据"""
        def query_builder():
            query = {}
            if task_id:
                query['task_id'] = task_id
            if status:
                query['status'] = status
            return query

        return self._export_data(self.site_repo, query_builder, 'sites', format, fields)

    @audit_log(action='export', resource='url')
    def export_urls(
        self,
        task_id: Optional[str] = None,
        domain: Optional[str] = None,
        format: str = 'json',
        fields: Optional[List[str]] = None
    ) -> str:
        """导出URL数据"""
        def query_builder():
            query = {}
            if task_id:
                query['task_id'] = task_id
            if domain:
                import re
                regex = f"^https?://([a-zA-Z0-9-]+\\.)*{re.escape(domain)}"
                query['url'] = {'$regex': regex}
            return query

        return self._export_data(self.url_repo, query_builder, 'urls', format, fields)

    @audit_log(action='export', resource='cert')
    def export_certs(
        self,
        task_id: Optional[str] = None,
        domain: Optional[str] = None,
        format: str = 'json',
        fields: Optional[List[str]] = None
    ) -> str:
        """导出证书数据"""
        def query_builder():
            query = {}
            if task_id:
                query['task_id'] = task_id
            if domain:
                query['domain'] = domain
            return query

        return self._export_data(self.cert_repo, query_builder, 'certs', format, fields)

    @audit_log(action='export', resource='task')
    def export_tasks(
        self,
        status: Optional[str] = None,
        format: str = 'json',
        fields: Optional[List[str]] = None
    ) -> str:
        """导出任务数据"""
        def query_builder():
            query = {}
            if status:
                query['status'] = status
            return query

        return self._export_data(self.task_repo, query_builder, 'tasks', format, fields)

    def cleanup_old_exports(self, max_age_days: int = 7) -> int:
        """
        清理过期的导出文件

        Args:
            max_age_days: 最大保留天数

        Returns:
            删除的文件数量
        """
        deleted_count = 0
        cutoff_time = datetime.now().timestamp() - (max_age_days * 86400)

        for filename in os.listdir(self.export_dir):
            file_path = os.path.join(self.export_dir, filename)
            if os.path.isfile(file_path):
                file_mtime = os.path.getmtime(file_path)
                if file_mtime < cutoff_time:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                    except Exception as e:
                        logger.error(f"Failed to delete {file_path}: {e}")

        logger.info(f"Cleaned up {deleted_count} old export files")
        return deleted_count

    def get_export_info(self, file_path: str) -> Dict[str, Any]:
        """
        获取导出文件信息

        Args:
            file_path: 文件路径

        Returns:
            文件信息字典
        """
        if not os.path.exists(file_path):
            return {}

        stat = os.stat(file_path)
        return {
            'file_path': file_path,
            'file_name': os.path.basename(file_path),
            'file_size': stat.st_size,
            'created_at': datetime.fromtimestamp(stat.st_ctime).isoformat(),
            'modified_at': datetime.fromtimestamp(stat.st_mtime).isoformat()
        }
