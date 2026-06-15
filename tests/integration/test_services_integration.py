# -*- coding: utf-8 -*-
"""
服务层集成测试
测试服务与数据库的交互
"""
import pytest
from unittest.mock import MagicMock, patch

# 标记需要数据库连接的测试
pytestmark = pytest.mark.integration


@pytest.fixture
def mock_db():
    """模拟数据库"""
    db = MagicMock()
    return db


@pytest.fixture
def mock_task_repo(mock_db):
    """模拟任务仓库"""
    from app.database.repositories import TaskRepository
    repo = MagicMock(spec=TaskRepository)
    return repo


@pytest.fixture
def mock_user_repo(mock_db):
    """模拟用户仓库"""
    from app.database.repositories import UserRepository
    repo = MagicMock(spec=UserRepository)
    return repo


class TestTaskServiceIntegration:
    """任务服务集成测试"""

    def test_create_and_retrieve_task(self, mock_task_repo):
        """测试创建和检索任务"""
        from app.services.task_service import TaskService

        # 模拟仓库行为
        mock_task_repo.insert_one.return_value = "task_id_123"
        mock_task_repo.find_by_task_id.return_value = {
            "task_id": "task_id_123",
            "target": "example.com",
            "status": "pending",
        }

        service = TaskService(mock_task_repo)

        # 创建任务
        result = service.create_task(
            target="example.com",
            task_type="domain",
            created_by="testuser",
        )
        assert result["task_id"] == "task_id_123"

        # 检索任务
        task = service.get_task_status("task_id_123")
        assert task["target"] == "example.com"

    def test_task_lifecycle(self, mock_task_repo):
        """测试任务生命周期"""
        from app.services.task_service import TaskService

        mock_task_repo.insert_one.return_value = "task_123"
        mock_task_repo.find_by_task_id.return_value = {
            "task_id": "task_123",
            "status": "pending",
        }
        mock_task_repo.update_status.return_value = True

        service = TaskService(mock_task_repo)

        # 创建
        service.create_task("example.com", "domain", "testuser")

        # 开始
        mock_task_repo.find_by_task_id.return_value["status"] = "running"
        result = service.get_task_status("task_123")
        assert result["status"] == "running"

        # 完成
        mock_task_repo.find_by_task_id.return_value["status"] = "completed"
        result = service.get_task_status("task_123")
        assert result["status"] == "completed"


class TestUserServiceIntegration:
    """用户服务集成测试"""

    def test_user_authentication_flow(self, mock_user_repo):
        """测试用户认证流程"""
        from app.services.user_service import UserService

        mock_user_repo.find_by_username.return_value = {
            "username": "testuser",
            "password_hash": "$2b$12$test_hash",
            "is_active": True,
            "role": "admin",
        }

        service = UserService(mock_user_repo)

        with patch("app.services.user_service.verify_password", return_value=True):
            user = service.authenticate("testuser", "password")
            assert user["username"] == "testuser"

    def test_user_creation_flow(self, mock_user_repo):
        """测试用户创建流程"""
        from app.services.user_service import UserService

        mock_user_repo.find_by_username.return_value = None
        mock_user_repo.insert_one.return_value = "user_id_123"

        service = UserService(mock_user_repo)

        result = service.create_user(
            username="newuser",
            password="password123",
            role="viewer",
        )
        assert result["user_id"] == "user_id_123"


class TestDomainServiceIntegration:
    """域名服务集成测试"""

    def test_domain_enumeration_flow(self):
        """测试域名枚举流程"""
        from app.services.domain_service import DomainService

        task_repo = MagicMock()
        domain_repo = MagicMock()

        task_repo.find_by_task_id.return_value = {
            "task_id": "task_123",
            "status": "pending",
        }
        domain_repo.find_many.return_value = []

        service = DomainService(domain_repo, task_repo)

        result = service.enumerate_subdomains("task_123")
        assert result["task_id"] == "task_123"


class TestIPServiceIntegration:
    """IP服务集成测试"""

    def test_ip_scan_flow(self):
        """测试IP扫描流程"""
        from app.services.ip_service import IPService

        task_repo = MagicMock()
        ip_repo = MagicMock()

        task_repo.find_by_task_id.return_value = {
            "task_id": "task_123",
            "status": "pending",
        }
        ip_repo.find_many.return_value = []

        service = IPService(ip_repo, task_repo)

        result = service.scan_ip("task_123", "192.168.1.1")
        assert result["task_id"] == "task_123"
        assert result["ip"] == "192.168.1.1"


class TestSiteServiceIntegration:
    """站点服务集成测试"""

    def test_site_fetch_flow(self):
        """测试站点获取流程"""
        from app.services.site_service import SiteService

        task_repo = MagicMock()
        site_repo = MagicMock()

        task_repo.find_by_task_id.return_value = {
            "task_id": "task_123",
            "status": "pending",
        }
        site_repo.find_many.return_value = []

        service = SiteService(site_repo, task_repo)

        result = service.fetch_site("task_123", "https://example.com")
        assert result["task_id"] == "task_123"
        assert result["url"] == "https://example.com"


class TestSchedulerServiceIntegration:
    """调度器服务集成测试"""

    def test_scheduler_lifecycle(self):
        """测试调度器生命周期"""
        from app.services.scheduler_service import SchedulerService

        scheduler_repo = MagicMock()
        scheduler_repo.insert_one.return_value = "scheduler_id_123"
        scheduler_repo.update_scheduler_status.return_value = True

        service = SchedulerService(scheduler_repo)

        # 创建
        result = service.create_scheduler(
            name="每日资产监控",
            task_type="domain",
            target="example.com",
            interval_hours=24,
        )
        assert result["scheduler_id"] == "scheduler_id_123"

        # 更新状态
        result = service.update_scheduler_status("scheduler_id_123", "running")
        assert result is True


class TestExportServiceIntegration:
    """导出服务集成测试"""

    def test_export_flow(self):
        """测试导出流程"""
        from app.services.export_service import ExportService

        export_repo = MagicMock()
        export_repo.find_many.return_value = [
            {"domain": "example1.com"},
            {"domain": "example2.com"},
        ]

        service = ExportService(export_repo)

        result = service.export_data(
            data_type="domain",
            format="json",
            query={},
        )

        assert result["format"] == "json"
        assert len(result["data"]) == 2
