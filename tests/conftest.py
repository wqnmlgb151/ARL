# -*- coding: utf-8 -*-
"""
ARL测试配置
pytest fixtures和配置
"""

import os
import sys
import io
import pytest
from unittest.mock import MagicMock, patch
from typing import Generator

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Windows I/O 重定向修复：pytest 在 Windows 上会因 I/O 重定向冲突导致 ValueError
# 在 pytest 运行前恢复原始 stdout/stderr

# 保存原始 I/O
_original_stdout = sys.stdout
_original_stderr = sys.stderr


def _restore_io():
    """恢复原始 stdout/stderr，避免 pytest 的 I/O 重定向冲突"""
    if sys.platform == "win32":
        if hasattr(_original_stdout, "buffer"):
            sys.stdout = _original_stdout
        if hasattr(_original_stderr, "buffer"):
            sys.stderr = _original_stderr


# 在 pytest 启动前恢复 I/O
_restore_io()


# ============================================================================
# 基础Fixtures
# ============================================================================

@pytest.fixture
def app():
    """创建测试用Flask应用"""
    os.environ["TESTING"] = "true"
    os.environ["MONGO_URL"] = "mongodb://localhost:27017"
    os.environ["MONGO_DB"] = "arl_test"

    from app.main import create_app
    app = create_app()
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False

    yield app


@pytest.fixture
def client(app):
    """创建测试客户端"""
    return app.test_client()


@pytest.fixture
def runner(app):
    """创建CLI测试runner"""
    return app.test_cli_runner()


# ============================================================================
# Mock Fixtures
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock数据库连接"""
    with patch("app.database.connection.DatabaseManager") as mock:
        db_instance = MagicMock()
        mock.return_value = db_instance
        mock.is_initialized.return_value = True
        yield db_instance


@pytest.fixture
def mock_collection():
    """Mock MongoDB集合"""
    collection = MagicMock()
    collection.find_one.return_value = None
    collection.find.return_value = []
    collection.insert_one.return_value = MagicMock(inserted_id="test_id_123")
    collection.update_one.return_value = MagicMock(modified_count=1)
    collection.delete_one.return_value = MagicMock(deleted_count=1)
    collection.count_documents.return_value = 0
    collection.aggregate.return_value = []
    return collection


@pytest.fixture
def mock_user_repo(mock_collection):
    """Mock用户Repository"""
    with patch("app.services.user_service.UserRepository") as mock:
        repo = MagicMock()
        repo.find_by_username.return_value = None
        repo.find_by_token.return_value = None
        repo.find_by_api_key.return_value = None
        repo.insert_one.return_value = "user_id_123"
        repo.update_one.return_value = True
        repo.collection = mock_collection
        mock.return_value = repo
        yield repo


@pytest.fixture
def mock_task_repo(mock_collection):
    """Mock任务Repository"""
    with patch("app.services.task_service.TaskRepository") as mock:
        repo = MagicMock()
        repo.find_by_task_id.return_value = None
        repo.insert_one.return_value = "task_id_123"
        repo.update_one.return_value = True
        repo.update_status.return_value = True
        repo.find_many.return_value = []
        repo.count.return_value = 0
        repo.get_statistics.return_value = {"total": 0}
        repo.collection = mock_collection
        mock.return_value = repo
        yield repo


@pytest.fixture
def mock_domain_repo(mock_collection):
    """Mock域名Repository"""
    with patch("app.services.domain_service.DomainRepository") as mock:
        repo = MagicMock()
        repo.find_by_domain.return_value = None
        repo.find_by_task.return_value = []
        repo.insert_one.return_value = "domain_id_123"
        repo.find_many.return_value = []
        repo.count.return_value = 0
        repo.collection = mock_collection
        mock.return_value = repo
        yield repo


@pytest.fixture
def mock_ip_repo(mock_collection):
    """Mock IP Repository"""
    with patch("app.services.ip_service.IPRepository") as mock:
        repo = MagicMock()
        repo.find_by_ip.return_value = None
        repo.find_by_task.return_value = []
        repo.insert_one.return_value = "ip_id_123"
        repo.find_many.return_value = []
        repo.count.return_value = 0
        repo.collection = mock_collection
        mock.return_value = repo
        yield repo


@pytest.fixture
def mock_site_repo(mock_collection):
    """Mock站点Repository"""
    with patch("app.services.site_service.SiteRepository") as mock:
        repo = MagicMock()
        repo.find_by_url.return_value = None
        repo.find_by_task.return_value = []
        repo.insert_one.return_value = "site_id_123"
        repo.find_many.return_value = []
        repo.count.return_value = 0
        repo.collection = mock_collection
        mock.return_value = repo
        yield repo


# ============================================================================
# 测试数据Fixtures
# ============================================================================

@pytest.fixture
def sample_user():
    """示例用户数据"""
    return {
        "username": "testuser",
        "password_hash": "$2b$12$test_hash",
        "role": "admin",
        "api_key": "test_api_key_123",
        "is_active": True,
    }


@pytest.fixture
def sample_task():
    """示例任务数据"""
    return {
        "task_id": "task_abc123",
        "target": "example.com",
        "task_type": "domain",
        "status": "pending",
        "options": {},
        "created_by": "testuser",
        "result_count": 0,
    }


@pytest.fixture
def sample_domain():
    """示例域名数据"""
    return {
        "domain": "example.com",
        "ip": ["93.184.216.34"],
        "task_id": "task_abc123",
    }


@pytest.fixture
def sample_ip():
    """示例IP数据"""
    return {
        "ip": "93.184.216.34",
        "task_id": "task_abc123",
        "geoip": {
            "country_code": "US",
            "country_name": "United States",
        },
        "asn": {
            "number": 13335,
            "organization": "Cloudflare, Inc.",
        },
    }


@pytest.fixture
def sample_site():
    """示例站点数据"""
    return {
        "url": "https://example.com",
        "task_id": "task_abc123",
        "status": "active",
        "title": "Example Domain",
        "http_status": 200,
    }


@pytest.fixture
def valid_api_key():
    """有效的API Key"""
    return "test_api_key_123"


@pytest.fixture
def valid_token():
    """有效的Token"""
    return "valid_token_xyz789"


# ============================================================================
# 认证Fixtures
# ============================================================================

@pytest.fixture
def auth_headers(valid_api_key):
    """认证请求头"""
    return {
        "X-API-Key": valid_api_key,
        "Content-Type": "application/json",
    }


@pytest.fixture
def mock_authenticated_user(sample_user, valid_token):
    """模拟已认证用户"""
    with patch("app.core.permissions.check_api_key", return_value=True):
        with patch("flask.g") as mock_g:
            mock_g.current_user = sample_user
            yield sample_user


# ============================================================================
# 钩子函数
# ============================================================================

def pytest_configure(config):
    """pytest配置钩子"""
    config.addinivalue_line("markers", "unit: 单元测试（无I/O）")
    config.addinivalue_line("markers", "integration: 集成测试（需要数据库）")
    config.addinivalue_line("markers", "slow: 慢测试（>1秒）")
    config.addinivalue_line("markers", "security: 安全相关测试")
    config.addinivalue_line("markers", "api: API端点测试")


def pytest_collection_modifyitems(config, items):
    """根据标记分类测试"""
    for item in items:
        # 根据路径自动添加标记
        if "unit" in item.nodeid:
            item.add_marker(pytest.mark.unit)
        elif "integration" in item.nodeid:
            item.add_marker(pytest.mark.integration)
        elif "security" in item.nodeid:
            item.add_marker(pytest.mark.security)


@pytest.fixture(autouse=True)
def cleanup():
    """每个测试后的清理"""
    yield
    # 清理临时状态
    pass
