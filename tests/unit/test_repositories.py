# -*- coding: utf-8 -*-
"""
仓库层数据访问测试
"""
import pytest
from unittest.mock import MagicMock, patch
from app.database.repositories import (
    BaseRepository,
    TaskRepository,
    DomainRepository,
    IPRepository,
    SiteRepository,
    UserRepository,
    SchedulerRepository,
)


class TestBaseRepository:
    """基础仓库测试"""

    def test_init_requires_collection_name(self):
        """测试初始化需要collection_name"""
        with pytest.raises(ValueError, match="collection_name must be set"):
            BaseRepository()

    @patch('app.database.connection.get_collection')
    def test_find_by_id(self, mock_get_collection):
        """测试按ID查找"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.find_one.return_value = {"_id": "507f1f77bcf86cd799439011", "name": "test"}

        repo = TaskRepository()
        result = repo.find_by_id("507f1f77bcf86cd799439011")

        assert result["name"] == "test"
        mock_collection.find_one.assert_called_once()

    @patch('app.database.connection.get_collection')
    def test_find_by_id_invalid_format(self, mock_get_collection):
        """测试按ID查找 - 无效ID格式"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection

        repo = TaskRepository()
        from app.core.exceptions import ValidationException
        with pytest.raises(ValidationException, match="Invalid ID format"):
            repo.find_by_id("invalid_id_format")

    @patch('app.database.connection.get_collection')
    def test_find_one(self, mock_get_collection):
        """测试查找单个文档"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.find_one.return_value = {"key": "value"}

        repo = TaskRepository()
        result = repo.find_one({"key": "value"})

        assert result["key"] == "value"
        mock_collection.find_one.assert_called_once_with({"key": "value"})

    @patch('app.database.connection.get_collection')
    def test_find_many(self, mock_get_collection):
        """测试查找多个文档"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        cursor = MagicMock()
        cursor.skip.return_value = cursor
        cursor.limit.return_value = cursor
        cursor.sort.return_value = cursor
        cursor.__iter__ = MagicMock(return_value=iter([
            {"_id": "1", "name": "a"},
            {"_id": "2", "name": "b"},
        ]))
        mock_collection.find.return_value = cursor

        repo = TaskRepository()
        result = repo.find_many({}, skip=0, limit=10)

        assert len(result) == 2

    @patch('app.database.connection.get_collection')
    def test_insert_one(self, mock_get_collection):
        """测试插入单个文档"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.insert_one.return_value = MagicMock(inserted_id="new_id")

        repo = TaskRepository()
        result = repo.insert_one({"name": "test"})

        assert result == "new_id"
        mock_collection.insert_one.assert_called_once()

    @patch('app.database.connection.get_collection')
    def test_update_one(self, mock_get_collection):
        """测试更新单个文档"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        repo = TaskRepository()
        result = repo.update_one({"id": "123"}, {"$set": {"name": "updated"}})

        assert result is True
        mock_collection.update_one.assert_called_once()

    @patch('app.database.connection.get_collection')
    def test_delete_one(self, mock_get_collection):
        """测试删除单个文档"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.delete_one.return_value = MagicMock(deleted_count=1)

        repo = TaskRepository()
        result = repo.delete_one({"id": "123"})

        assert result is True
        mock_collection.delete_one.assert_called_once()

    @patch('app.database.connection.get_collection')
    def test_count(self, mock_get_collection):
        """测试计数"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.count_documents.return_value = 42

        repo = TaskRepository()
        result = repo.count({"status": "active"})

        assert result == 42
        mock_collection.count_documents.assert_called_once_with({"status": "active"})

    @patch('app.database.connection.get_collection')
    def test_aggregate(self, mock_get_collection):
        """测试聚合"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.aggregate.return_value = [
            {"_id": "group1", "count": 10},
            {"_id": "group2", "count": 20},
        ]

        repo = TaskRepository()
        result = repo.aggregate([{"$group": {"_id": "$status", "count": {"$sum": 1}}}])

        assert len(result) == 2

    @patch('app.database.connection.get_collection')
    def test_bulk_write(self, mock_get_collection):
        """测试批量写入"""
        from pymongo import UpdateOne
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        operations = [
            UpdateOne({"id": "1"}, {"$set": {"name": "a"}}),
            UpdateOne({"id": "2"}, {"$set": {"name": "b"}}),
        ]
        mock_collection.bulk_write.return_value = MagicMock(modified_count=2)

        repo = TaskRepository()
        result = repo.bulk_write(operations)

        assert result["modified_count"] == 2

    @patch('app.database.connection.get_collection')
    def test_bulk_upsert(self, mock_get_collection):
        """测试批量更新插入"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        documents = [
            {"id": "1", "name": "a"},
            {"id": "2", "name": "b"},
        ]
        mock_collection.bulk_write.return_value = MagicMock(upserted_count=2, modified_count=0)

        repo = TaskRepository()
        result = repo.bulk_upsert(documents, "id")

        assert result == 2

    @patch('app.database.connection.get_collection')
    def test_find_by_task(self, mock_get_collection):
        """测试按任务ID查找"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        cursor = MagicMock()
        cursor.skip.return_value = cursor
        cursor.limit.return_value = cursor
        cursor.sort.return_value = cursor
        cursor.__iter__ = MagicMock(return_value=iter([
            {"task_id": "task_123", "data": "a"},
            {"task_id": "task_123", "data": "b"},
        ]))
        mock_collection.find.return_value = cursor

        repo = TaskRepository()
        result = repo.find_by_task("task_123")

        assert len(result) == 2

    @patch('app.database.connection.get_collection')
    def test_get_statistics(self, mock_get_collection):
        """测试获取统计"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.aggregate.return_value = [
            {"_id": "status1", "count": 50},
            {"_id": "status2", "count": 50},
        ]

        repo = TaskRepository()
        result = repo.get_statistics()

        assert result["total"] == 100


class TestTaskRepository:
    """任务仓库测试"""

    @patch('app.database.connection.get_collection')
    def test_find_by_task_id(self, mock_get_collection):
        """测试按任务ID查找"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.find_one.return_value = {
            "task_id": "task_123",
            "target": "example.com",
        }

        repo = TaskRepository()
        result = repo.find_by_task_id("task_123")

        assert result["task_id"] == "task_123"
        mock_collection.find_one.assert_called_once_with({"task_id": "task_123"})

    @patch('app.database.connection.get_collection')
    def test_update_status(self, mock_get_collection):
        """测试更新状态"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.update_one.return_value = MagicMock(modified_count=1)

        repo = TaskRepository()
        from app.core.types import TaskStatus
        result = repo.update_status("task_123", TaskStatus.COMPLETED)

        assert result is True
        mock_collection.update_one.assert_called_once()

    @patch('app.database.connection.get_collection')
    def test_find_by_status(self, mock_get_collection):
        """测试按状态查找"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        cursor = MagicMock()
        cursor.skip.return_value = cursor
        cursor.limit.return_value = cursor
        cursor.sort.return_value = cursor
        cursor.__iter__ = MagicMock(return_value=iter([
            {"task_id": "task_1", "status": "pending"},
            {"task_id": "task_2", "status": "pending"},
        ]))
        mock_collection.find.return_value = cursor

        repo = TaskRepository()
        from app.core.types import TaskStatus
        result = repo.find_by_status(TaskStatus.PENDING)

        assert len(result) == 2


class TestDomainRepository:
    """域名仓库测试"""

    @patch('app.database.connection.get_collection')
    def test_find_by_domain(self, mock_get_collection):
        """测试按域名查找"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.find_one.return_value = {
            "domain": "example.com",
            "ip": ["93.184.216.34"],
        }

        repo = DomainRepository()
        result = repo.find_by_domain("example.com")

        assert result["domain"] == "example.com"
        mock_collection.find_one.assert_called_once_with({"domain": "example.com"})

    @patch('app.database.connection.get_collection')
    def test_find_by_task(self, mock_get_collection):
        """测试按任务ID查找"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        cursor = MagicMock()
        cursor.skip.return_value = cursor
        cursor.limit.return_value = cursor
        cursor.sort.return_value = cursor
        cursor.__iter__ = MagicMock(return_value=iter([
            {"domain": "a.example.com", "task_id": "task_123"},
            {"domain": "b.example.com", "task_id": "task_123"},
        ]))
        mock_collection.find.return_value = cursor

        repo = DomainRepository()
        result = repo.find_by_task("task_123")

        assert len(result) == 2

    @patch('app.database.connection.get_collection')
    def test_find_by_ip(self, mock_get_collection):
        """测试按IP查找"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        cursor = MagicMock()
        cursor.skip.return_value = cursor
        cursor.limit.return_value = cursor
        cursor.sort.return_value = cursor
        cursor.__iter__ = MagicMock(return_value=iter([
            {"domain": "a.com", "ip": ["192.168.1.1"]},
            {"domain": "b.com", "ip": ["192.168.1.1"]},
        ]))
        mock_collection.find.return_value = cursor

        repo = DomainRepository()
        result = repo.find_by_ip("192.168.1.1")

        assert len(result) == 2


class TestIPRepository:
    """IP仓库测试"""

    @patch('app.database.connection.get_collection')
    def test_find_by_ip(self, mock_get_collection):
        """测试按IP查找"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.find_one.return_value = {
            "ip": "93.184.216.34",
            "geoip": {"country": "US"},
        }

        repo = IPRepository()
        result = repo.find_by_ip("93.184.216.34")

        assert result["ip"] == "93.184.216.34"
        mock_collection.find_one.assert_called_once_with({"ip": "93.184.216.34"})

    @patch('app.database.connection.get_collection')
    def test_find_by_task(self, mock_get_collection):
        """测试按任务ID查找"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        cursor = MagicMock()
        cursor.skip.return_value = cursor
        cursor.limit.return_value = cursor
        cursor.sort.return_value = cursor
        cursor.__iter__ = MagicMock(return_value=iter([
            {"ip": "192.168.1.1", "task_id": "task_123"},
            {"ip": "192.168.1.2", "task_id": "task_123"},
        ]))
        mock_collection.find.return_value = cursor

        repo = IPRepository()
        result = repo.find_by_task("task_123")

        assert len(result) == 2


class TestSiteRepository:
    """站点仓库测试"""

    @patch('app.database.connection.get_collection')
    def test_find_by_url(self, mock_get_collection):
        """测试按URL查找"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.find_one.return_value = {
            "url": "https://example.com",
            "title": "Example Domain",
        }

        repo = SiteRepository()
        result = repo.find_by_url("https://example.com")

        assert result["url"] == "https://example.com"
        mock_collection.find_one.assert_called_once_with({"url": "https://example.com"})

    @patch('app.database.connection.get_collection')
    def test_find_by_task(self, mock_get_collection):
        """测试按任务ID查找"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        cursor = MagicMock()
        cursor.skip.return_value = cursor
        cursor.limit.return_value = cursor
        cursor.sort.return_value = cursor
        cursor.__iter__ = MagicMock(return_value=iter([
            {"url": "https://a.com", "task_id": "task_123"},
            {"url": "https://b.com", "task_id": "task_123"},
        ]))
        mock_collection.find.return_value = cursor

        repo = SiteRepository()
        result = repo.find_by_task("task_123")

        assert len(result) == 2


class TestUserRepository:
    """用户仓库测试"""

    @patch('app.database.connection.get_collection')
    def test_find_by_username(self, mock_get_collection):
        """测试按用户名查找"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.find_one.return_value = {
            "username": "testuser",
            "role": "admin",
        }

        repo = UserRepository()
        result = repo.find_by_username("testuser")

        assert result["username"] == "testuser"
        mock_collection.find_one.assert_called_once_with({"username": "testuser"})

    @patch('app.database.connection.get_collection')
    def test_find_by_token(self, mock_get_collection):
        """测试按Token查找"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.find_one.return_value = {
            "username": "testuser",
            "token": "token_123",
        }

        repo = UserRepository()
        result = repo.find_by_token("token_123")

        assert result["username"] == "testuser"
        mock_collection.find_one.assert_called_once_with({"token": "token_123"})

    @patch('app.database.connection.get_collection')
    def test_find_by_api_key(self, mock_get_collection):
        """测试按API Key查找"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.find_one.return_value = {
            "username": "testuser",
            "api_key": "api_key_123",
        }

        repo = UserRepository()
        result = repo.find_by_api_key("api_key_123")

        assert result["username"] == "testuser"
        mock_collection.find_one.assert_called_once_with({"api_key": "api_key_123"})


class TestSchedulerRepository:
    """调度器仓库测试"""

    @patch('app.database.connection.get_collection')
    def test_find_by_task(self, mock_get_collection):
        """测试按任务ID查找"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        mock_collection.find_one.return_value = {
            "task_id": "task_123",
            "scheduler_id": "scheduler_123",
        }

        repo = SchedulerRepository()
        result = repo.find_by_task("task_123")

        assert result["task_id"] == "task_123"
        mock_collection.find_one.assert_called_once_with({"task_id": "task_123"})

    @patch('app.database.connection.get_collection')
    def test_find_active(self, mock_get_collection):
        """测试查找活跃调度器"""
        mock_collection = MagicMock()
        mock_get_collection.return_value = mock_collection
        cursor = MagicMock()
        cursor.skip.return_value = cursor
        cursor.limit.return_value = cursor
        cursor.sort.return_value = cursor
        cursor.__iter__ = MagicMock(return_value=iter([
            {"scheduler_id": "s1", "status": "active"},
            {"scheduler_id": "s2", "status": "active"},
        ]))
        mock_collection.find.return_value = cursor

        repo = SchedulerRepository()
        result = repo.find_active()

        assert len(result) == 2
