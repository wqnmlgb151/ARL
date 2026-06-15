# -*- coding: utf-8 -*-
"""
服务层业务逻辑测试
"""
import pytest
from unittest.mock import MagicMock, patch
from app.services.task_service import TaskService
from app.services.user_service import UserService
from app.services.domain_service import DomainService
from app.services.ip_service import IPService
from app.services.site_service import SiteService
from app.services.scheduler_service import SchedulerService
from app.services.export_service import ExportService
from app.core.types import TaskStatus, TaskType
from app.core.exceptions import (
    ValidationException,
    NotFoundException,
    AuthenticationException,
)


class TestTaskService:
    """任务服务测试"""

    def setup_method(self):
        """测试前准备"""
        self.repo = MagicMock()
        self.service = TaskService()
        self.service.repo = self.repo

    def test_create_task_success(self):
        """测试成功创建任务"""
        self.repo.insert_one.return_value = "task_doc_id"

        result = self.service.create_task(
            target="example.com",
            task_type=TaskType.DOMAIN,
            created_by="testuser",
        )

        # 任务ID是UUID格式
        assert "task_id" in result
        assert result["target"] == "example.com"
        self.repo.insert_one.assert_called_once()

    def test_create_task_invalid_target(self):
        """测试无效目标创建任务"""
        with pytest.raises(ValidationException):
            self.service.create_task(
                target="",
                task_type=TaskType.DOMAIN,
                created_by="testuser",
            )

    def test_get_task(self):
        """测试获取任务"""
        self.repo.find_by_task_id.return_value = {
            "task_id": "task_123",
            "status": "running",
            "target": "example.com",
        }

        result = self.service.get_task("task_123")

        assert result["status"] == "running"
        assert result["target"] == "example.com"

    def test_get_task_not_found(self):
        """测试获取不存在的任务"""
        self.repo.find_by_task_id.return_value = None

        with pytest.raises(NotFoundException):
            self.service.get_task("nonexistent")

    def test_cancel_task(self):
        """测试取消任务"""
        self.repo.find_by_task_id.return_value = {
            "task_id": "task_123",
            "status": "running",
        }
        self.repo.update_one.return_value = True

        result = self.service.cancel_task("task_123")

        assert result is True
        self.repo.update_one.assert_called_once()

    def test_list_tasks(self):
        """测试列出任务"""
        self.repo.find_many.return_value = [
            {"task_id": "task_1", "target": "example1.com"},
            {"task_id": "task_2", "target": "example2.com"},
        ]

        result = self.service.list_tasks()

        assert len(result) == 2

    def test_count_tasks(self):
        """测试统计任务数量"""
        self.repo.count.return_value = 42

        result = self.service.count_tasks()

        assert result == 42

    def test_get_task_statistics(self):
        """测试获取任务统计"""
        self.repo.get_statistics.return_value = {
            "total": 100,
            "pending": 20,
            "running": 10,
            "completed": 60,
            "failed": 10,
        }

        result = self.service.get_statistics()

        assert result["total"] == 100
        assert result["completed"] == 60


class TestUserService:
    """用户服务测试"""

    def setup_method(self):
        """测试前准备"""
        self.repo = MagicMock()
        self.service = UserService()
        self.service.repo = self.repo

    def test_authenticate_success(self):
        """测试成功认证"""
        self.repo.find_by_username.return_value = {
            "username": "testuser",
            "password_hash": "$2b$12$test_hash",
            "is_active": True,
        }

        with patch("app.services.user_service.UserService._verify_password", return_value=True):
            result, token = self.service.authenticate("testuser", "password")

        assert result is not None
        assert result["username"] == "testuser"

    def test_authenticate_wrong_password(self):
        """测试密码错误"""
        self.repo.find_by_username.return_value = {
            "username": "testuser",
            "password_hash": "$2b$12$test_hash",
            "is_active": True,
        }

        with patch("app.services.user_service.UserService._verify_password", return_value=False):
            with pytest.raises(AuthenticationException):
                self.service.authenticate("testuser", "wrong_password")

    def test_authenticate_user_not_found(self):
        """测试用户不存在"""
        self.repo.find_by_username.return_value = None

        with pytest.raises(AuthenticationException):
            self.service.authenticate("nonexistent", "password")

    def test_authenticate_inactive_user(self):
        """测试非活跃用户"""
        self.repo.find_by_username.return_value = {
            "username": "testuser",
            "password_hash": "$2b$12$test_hash",
            "is_active": False,
        }

        with pytest.raises(AuthenticationException):
            self.service.authenticate("testuser", "password")

    def test_create_user(self):
        """测试创建用户"""
        self.repo.find_by_username.return_value = None
        self.repo.insert_one.return_value = "user_id_123"

        result = self.service.create_user(
            username="newuser",
            password="password123",
            role="viewer",
        )

        assert result["username"] == "newuser"
        self.repo.insert_one.assert_called_once()

    def test_create_user_duplicate(self):
        """测试创建重复用户"""
        self.repo.find_by_username.return_value = {
            "username": "testuser",
        }

        with pytest.raises(ValidationException):
            self.service.create_user(
                username="testuser",
                password="password123",
                role="viewer",
            )


class TestDomainService:
    """域名服务测试"""

    def setup_method(self):
        """测试前准备"""
        self.repo = MagicMock()
        self.task_repo = MagicMock()
        self.service = DomainService()
        self.service.repo = self.repo
        self.service.task_repo = self.task_repo

    def test_find_by_task(self):
        """测试按任务ID查找域名"""
        self.task_repo.find_by_task_id.return_value = {
            "task_id": "task_123",
            "status": "pending",
        }
        self.repo.find_by_task.return_value = []

        result = self.service.find_by_task("task_123")

        assert result == []

    def test_get_domain_info(self):
        """测试获取域名信息"""
        self.repo.find_by_domain.return_value = {
            "domain": "example.com",
            "ip": ["93.184.216.34"],
        }

        with patch('app.services.domain_service.validate_domain'):
            result = self.service.get_domain_info("example.com")

        assert result["domain"] == "example.com"
        assert "93.184.216.34" in result["ip"]

    def test_find_subdomains(self):
        """测试查找子域名"""
        self.repo.find_subdomains.return_value = [
            {"domain": "sub1.example.com"},
            {"domain": "sub2.example.com"},
        ]

        with patch('app.services.domain_service.validate_domain'):
            result = self.service.find_subdomains("example.com")

        assert len(result) == 2


class TestIPService:
    """IP服务测试"""

    def setup_method(self):
        """测试前准备"""
        self.repo = MagicMock()
        self.task_repo = MagicMock()
        self.service = IPService()
        self.service.repo = self.repo
        self.service.task_repo = self.task_repo

    def test_find_by_task(self):
        """测试按任务ID查找IP"""
        self.task_repo.find_by_task_id.return_value = {
            "task_id": "task_123",
            "status": "pending",
        }
        self.repo.find_by_task.return_value = []

        result = self.service.find_by_task("task_123")

        assert result == []

    def test_get_ip_info(self):
        """测试获取IP信息"""
        self.repo.find_by_ip.return_value = {
            "ip": "93.184.216.34",
            "geoip": {"country": "US"},
        }

        result = self.service.get_ip_info("93.184.216.34")

        assert result["ip"] == "93.184.216.34"

    def test_find_by_asn(self):
        """测试按ASN查找IP"""
        self.repo.find_by_asn.return_value = [
            {"ip": "192.168.1.1", "asn": {"number": "AS12345"}},
            {"ip": "192.168.1.2", "asn": {"number": "AS12345"}},
        ]

        result = self.service.find_by_asn("AS12345")

        assert len(result) == 2


class TestSiteService:
    """站点服务测试"""

    def setup_method(self):
        """测试前准备"""
        self.repo = MagicMock()
        self.task_repo = MagicMock()
        self.service = SiteService()
        self.service.repo = self.repo
        self.service.task_repo = self.task_repo

    def test_find_by_task(self):
        """测试按任务ID查找站点"""
        self.task_repo.find_by_task_id.return_value = {
            "task_id": "task_123",
            "status": "pending",
        }
        self.repo.find_by_task.return_value = []

        result = self.service.find_by_task("task_123")

        assert result == []

    def test_get_site_info(self):
        """测试获取站点信息"""
        self.repo.find_by_url.return_value = {
            "url": "https://example.com",
            "title": "Example Domain",
            "http_status": 200,
        }

        result = self.service.get_site_info("https://example.com")

        assert result["url"] == "https://example.com"
        assert result["title"] == "Example Domain"

    def test_find_by_status(self):
        """测试按状态查找站点"""
        self.repo.find_by_status.return_value = [
            {"url": "https://a.com", "status": "active"},
            {"url": "https://b.com", "status": "active"},
        ]

        result = self.service.find_by_status("active")

        assert len(result) == 2


class TestSchedulerService:
    """调度器服务测试"""

    def setup_method(self):
        """测试前准备"""
        self.repo = MagicMock()
        self.service = SchedulerService()
        self.service.repo = self.repo

    def test_create_scheduler(self):
        """测试创建调度任务"""
        self.repo.insert_one.return_value = "scheduler_doc_id"

        result = self.service.create_scheduler(
            target="example.com",
            task_type=TaskType.DOMAIN,
            interval_hours=24,
        )

        assert result["target"] == "example.com"
        self.repo.insert_one.assert_called_once()

    def test_find_active(self):
        """测试查找活跃调度任务"""
        self.repo.find_active.return_value = [
            {"scheduler_id": "s1", "status": "active"},
            {"scheduler_id": "s2", "status": "active"},
        ]

        result = self.service.find_active()

        assert len(result) == 2

    def test_update_scheduler_status(self):
        """测试更新调度器状态"""
        self.repo.find_by_id.return_value = {
            "scheduler_id": "scheduler_123",
            "interval_hours": 24,
        }
        self.repo.update_by_id.return_value = True

        result = self.service.update_scheduler_status("scheduler_123", "running")

        assert result is True
        self.repo.update_by_id.assert_called_once()


class TestExportService:
    """导出服务测试"""

    def setup_method(self):
        """测试前准备"""
        self.domain_repo = MagicMock()
        self.ip_repo = MagicMock()
        with patch('app.services.export_service.Config') as mock_config:
            mock_config.BASE_DIR = '/tmp/test'
            self.service = ExportService()
        self.service._domain_repo = self.domain_repo
        self.service._ip_repo = self.ip_repo

    def test_export_domains_json(self):
        """测试导出域名JSON"""
        self.domain_repo.find_many.return_value = [
            {"domain": "example1.com"},
            {"domain": "example2.com"},
        ]

        result = self.service.export_domains(format="json")

        assert result.endswith(".json")
        self.domain_repo.find_many.assert_called_once()

    def test_export_ips_csv(self):
        """测试导出IP CSV"""
        self.ip_repo.find_many.return_value = [
            {"ip": "192.168.1.1"},
            {"ip": "192.168.1.2"},
        ]

        result = self.service.export_ips(format="csv")

        assert result.endswith(".csv")
        self.ip_repo.find_many.assert_called_once()

    def test_export_domains_with_filter(self):
        """测试带过滤器的域名导出"""
        self.domain_repo.find_many.return_value = [
            {"domain": "example.com"},
        ]

        result = self.service.export_domains(
            task_id="task_123",
            format="json",
        )

        assert result.endswith(".json")

    def test_export_invalid_format(self):
        """测试无效格式"""
        with pytest.raises(ValidationException):
            self.service.export_domains(
                format="invalid",
            )
