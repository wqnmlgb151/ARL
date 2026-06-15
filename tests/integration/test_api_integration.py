# -*- coding: utf-8 -*-
"""
API集成测试
测试API端点的完整流程
"""
import pytest
import json
from unittest.mock import MagicMock, patch

# 标记需要数据库连接的测试
pytestmark = pytest.mark.integration


@pytest.fixture
def app():
    """创建测试应用"""
    from app.main import create_app
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False
    return app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def auth_headers():
    """认证头"""
    return {
        "X-API-Key": "test_api_key_123",
        "Content-Type": "application/json",
    }


class TestTaskAPI:
    """任务API测试"""

    def test_create_task(self, client, auth_headers):
        """测试创建任务"""
        with patch("app.routes.task.TaskService") as mock_service:
            mock_service.return_value.create_task.return_value = {
                "task_id": "task_123",
            }

            response = client.post(
                "/api/task/",
                headers=auth_headers,
                data=json.dumps({
                    "target": "example.com",
                    "task_type": "domain",
                }),
            )

            assert response.status_code in [200, 201]

    def test_get_task_status(self, client, auth_headers):
        """测试获取任务状态"""
        with patch("app.routes.task.TaskService") as mock_service:
            mock_service.return_value.get_task_status.return_value = {
                "task_id": "task_123",
                "status": "running",
                "progress": 50,
            }

            response = client.get(
                "/api/task/task_123/status",
                headers=auth_headers,
            )

            assert response.status_code == 200

    def test_list_tasks(self, client, auth_headers):
        """测试列出任务"""
        with patch("app.routes.task.TaskService") as mock_service:
            mock_service.return_value.list_tasks.return_value = {
                "tasks": [],
                "total": 0,
            }

            response = client.get(
                "/api/task/",
                headers=auth_headers,
            )

            assert response.status_code == 200

    def test_cancel_task(self, client, auth_headers):
        """测试取消任务"""
        with patch("app.routes.task.TaskService") as mock_service:
            mock_service.return_value.cancel_task.return_value = True

            response = client.post(
                "/api/task/task_123/cancel",
                headers=auth_headers,
            )

            assert response.status_code == 200


class TestDomainAPI:
    """域名API测试"""

    def test_query_domain(self, client, auth_headers):
        """测试查询域名"""
        with patch("app.routes.domain.DomainService") as mock_service:
            mock_service.return_value.query_domain_info.return_value = {
                "domain": "example.com",
                "ip": ["93.184.216.34"],
            }

            response = client.get(
                "/api/domain/example.com",
                headers=auth_headers,
            )

            assert response.status_code == 200


class TestIPAPI:
    """IP API测试"""

    def test_query_ip(self, client, auth_headers):
        """测试查询IP"""
        with patch("app.routes.ip.IPService") as mock_service:
            mock_service.return_value.query_ip_info.return_value = {
                "ip": "93.184.216.34",
                "geoip": {"country": "US"},
            }

            response = client.get(
                "/api/ip/93.184.216.34",
                headers=auth_headers,
            )

            assert response.status_code == 200


class TestSiteAPI:
    """站点API测试"""

    def test_query_site(self, client, auth_headers):
        """测试查询站点"""
        with patch("app.routes.site.SiteService") as mock_service:
            mock_service.return_value.get_site_info.return_value = {
                "url": "https://example.com",
                "title": "Example Domain",
            }

            response = client.get(
                "/api/site/",
                headers=auth_headers,
                query_string={"url": "https://example.com"},
            )

            assert response.status_code == 200


class TestUserAPI:
    """用户API测试"""

    def test_login(self, client):
        """测试登录"""
        with patch("app.routes.user.UserService") as mock_service:
            mock_service.return_value.authenticate.return_value = {
                "username": "testuser",
                "token": "test_token",
            }

            response = client.post(
                "/api/user/login",
                data=json.dumps({
                    "username": "testuser",
                    "password": "password",
                }),
                content_type="application/json",
            )

            assert response.status_code in [200, 401]

    def test_logout(self, client, auth_headers):
        """测试登出"""
        response = client.post(
            "/api/user/logout",
            headers=auth_headers,
        )

        assert response.status_code == 200


class TestExportAPI:
    """导出API测试"""

    def test_export_data(self, client, auth_headers):
        """测试导出数据"""
        with patch("app.routes.export.ExportService") as mock_service:
            mock_service.return_value.export_data.return_value = {
                "format": "json",
                "data": [],
            }

            response = client.post(
                "/api/export/",
                headers=auth_headers,
                data=json.dumps({
                    "data_type": "domain",
                    "format": "json",
                }),
            )

            assert response.status_code == 200


class TestSchedulerAPI:
    """调度器API测试"""

    def test_list_schedulers(self, client, auth_headers):
        """测试列出调度器"""
        with patch("app.routes.scheduler.SchedulerService") as mock_service:
            mock_service.return_value.list_schedulers.return_value = []

            response = client.get(
                "/api/scheduler/",
                headers=auth_headers,
            )

            assert response.status_code == 200

    def test_create_scheduler(self, client, auth_headers):
        """测试创建调度器"""
        with patch("app.routes.scheduler.SchedulerService") as mock_service:
            mock_service.return_value.create_scheduler.return_value = {
                "scheduler_id": "scheduler_123",
            }

            response = client.post(
                "/api/scheduler/",
                headers=auth_headers,
                data=json.dumps({
                    "name": "测试调度",
                    "task_type": "domain",
                    "target": "example.com",
                    "interval_hours": 24,
                }),
            )

            assert response.status_code in [200, 201]


class TestAuthentication:
    """认证测试"""

    def test_unauthorized_access(self, client):
        """测试未授权访问"""
        response = client.get("/api/task/")
        assert response.status_code == 401

    def test_invalid_api_key(self, client):
        """测试无效API Key"""
        headers = {"X-API-Key": "invalid_key"}
        response = client.get("/api/task/", headers=headers)
        assert response.status_code == 401

    def test_authorized_access(self, client, auth_headers):
        """测试授权访问"""
        with patch("app.core.permissions.check_api_key", return_value=True):
            response = client.get("/api/task/", headers=auth_headers)
            assert response.status_code == 200


class TestErrorHandling:
    """错误处理测试"""

    def test_not_found(self, client, auth_headers):
        """测试404错误"""
        response = client.get(
            "/api/nonexistent",
            headers=auth_headers,
        )
        assert response.status_code == 404

    def test_validation_error(self, client, auth_headers):
        """测试验证错误"""
        response = client.post(
            "/api/task/",
            headers=auth_headers,
            data=json.dumps({
                "target": "",  # 无效目标
                "task_type": "domain",
            }),
        )
        assert response.status_code in [400, 422]

    def test_internal_error(self, client, auth_headers):
        """测试内部错误"""
        with patch("app.routes.task.TaskService") as mock_service:
            mock_service.side_effect = Exception("Internal error")

            response = client.get(
                "/api/task/",
                headers=auth_headers,
            )
            assert response.status_code == 500
