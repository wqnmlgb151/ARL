# -*- coding: utf-8 -*-
"""
导出服务测试
"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.export_service import ExportService
from app.core.exceptions import ValidationException


class TestExportService:
    """导出服务测试"""

    def setup_method(self):
        """测试前准备"""
        self.domain_repo = MagicMock()
        self.ip_repo = MagicMock()
        self.site_repo = MagicMock()
        self.url_repo = MagicMock()
        self.cert_repo = MagicMock()
        self.task_repo = MagicMock()
        with patch('app.services.export_service.Config') as mock_config:
            mock_config.BASE_DIR = '/tmp/test'
            self.service = ExportService()
        self.service._domain_repo = self.domain_repo
        self.service._ip_repo = self.ip_repo
        self.service._site_repo = self.site_repo
        self.service._url_repo = self.url_repo
        self.service._cert_repo = self.cert_repo
        self.service._task_repo = self.task_repo

    def test_export_domains_json(self):
        """测试导出域名JSON格式"""
        self.domain_repo.find_many.return_value = [
            {"domain": "example1.com", "ip": ["1.1.1.1"]},
            {"domain": "example2.com", "ip": ["2.2.2.2"]},
        ]

        result = self.service.export_domains(format="json")

        assert result.endswith(".json")
        self.domain_repo.find_many.assert_called_once()

    def test_export_ips_csv(self):
        """测试导出IP CSV格式"""
        self.ip_repo.find_many.return_value = [
            {"ip": "192.168.1.1", "country": "US"},
            {"ip": "192.168.1.2", "country": "CN"},
        ]

        result = self.service.export_ips(format="csv")

        assert result.endswith(".csv")
        self.ip_repo.find_many.assert_called_once()

    def test_export_with_task_filter(self):
        """测试带任务过滤器的导出"""
        self.domain_repo.find_many.return_value = [
            {"domain": "example.com", "task_id": "task_123"},
        ]

        result = self.service.export_domains(task_id="task_123", format="json")

        assert result.endswith(".json")

    def test_export_empty_result(self):
        """测试空结果导出"""
        self.domain_repo.find_many.return_value = []

        result = self.service.export_domains(format="json")

        assert result.endswith(".json")

    def test_export_invalid_format(self):
        """测试无效格式"""
        with pytest.raises(ValidationException):
            self.service.export_domains(format="invalid")

    def test_export_sites(self):
        """测试导出站点数据"""
        self.site_repo.find_many.return_value = [
            {"url": "https://example.com", "title": "Example"},
        ]

        result = self.service.export_sites(format="json")

        assert result.endswith(".json")
        self.site_repo.find_many.assert_called_once()

    def test_export_urls(self):
        """测试导出URL数据"""
        self.url_repo.find_many.return_value = [
            {"url": "https://example.com/page1"},
            {"url": "https://example.com/page2"},
        ]

        result = self.service.export_urls(format="json")

        assert result.endswith(".json")
        self.url_repo.find_many.assert_called_once()

    def test_export_certs(self):
        """测试导出证书数据"""
        self.cert_repo.find_many.return_value = [
            {"serial_number": "123456789", "domain": "example.com"},
        ]

        result = self.service.export_certs(format="json")

        assert result.endswith(".json")
        self.cert_repo.find_many.assert_called_once()

    def test_export_tasks(self):
        """测试导出任务数据"""
        self.task_repo.find_many.return_value = [
            {"task_id": "task_123", "target": "example.com"},
        ]

        result = self.service.export_tasks(format="json")

        assert result.endswith(".json")
        self.task_repo.find_many.assert_called_once()

    def test_export_with_fields_selection(self):
        """测试带字段选择的导出"""
        self.domain_repo.find_many.return_value = [
            {"domain": "example.com", "ip": ["1.1.1.1"], "status": "active"},
        ]

        result = self.service.export_domains(
            format="json",
            fields=["domain", "ip"]
        )

        assert result.endswith(".json")

    def test_export_supported_formats(self):
        """测试支持的导出格式"""
        self.domain_repo.find_many.return_value = []

        json_result = self.service.export_domains(format="json")
        csv_result = self.service.export_domains(format="csv")

        assert json_result.endswith(".json")
        assert csv_result.endswith(".csv")
