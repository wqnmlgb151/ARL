# -*- coding: utf-8 -*-
"""
DatabaseManager Sanitizer 集成测试
验证 NoSQL 注入防护已正确集成到 DatabaseManager
"""
import pytest
from unittest.mock import MagicMock, patch
from app.database.connection import DatabaseManager
from app.utils.sanitizer import MongoSanitizer


class TestDatabaseManagerSanitizerIntegration:
    """DatabaseManager Sanitizer 集成测试"""

    def setup_method(self):
        """测试前准备"""
        DatabaseManager._instance = None
        DatabaseManager._client = None
        DatabaseManager._db = None

    def teardown_method(self):
        """测试后清理"""
        DatabaseManager._instance = None
        DatabaseManager._client = None
        DatabaseManager._db = None

    def test_safe_find_one_method_exists(self):
        """测试 safe_find_one 方法存在"""
        assert hasattr(DatabaseManager, 'safe_find_one')
        assert callable(DatabaseManager.safe_find_one)

    def test_safe_find_method_exists(self):
        """测试 safe_find 方法存在"""
        assert hasattr(DatabaseManager, 'safe_find')
        assert callable(DatabaseManager.safe_find)

    def test_safe_insert_one_method_exists(self):
        """测试 safe_insert_one 方法存在"""
        assert hasattr(DatabaseManager, 'safe_insert_one')
        assert callable(DatabaseManager.safe_insert_one)

    def test_safe_update_one_method_exists(self):
        """测试 safe_update_one 方法存在"""
        assert hasattr(DatabaseManager, 'safe_update_one')
        assert callable(DatabaseManager.safe_update_one)

    def test_safe_delete_one_method_exists(self):
        """测试 safe_delete_one 方法存在"""
        assert hasattr(DatabaseManager, 'safe_delete_one')
        assert callable(DatabaseManager.safe_delete_one)

    @patch('app.database.connection.MongoSanitizer.safe_find_one')
    def test_safe_find_one_calls_sanitizer(self, mock_safe_find_one):
        """测试 safe_find_one 调用 sanitizer"""
        mock_safe_find_one.return_value = {"result": "test"}

        # 初始化 DatabaseManager
        with patch('app.database.connection.MongoClient') as mock_client:
            mock_client.return_value = MagicMock()
            DatabaseManager.init()

            # 调用 safe_find_one
            result = DatabaseManager.safe_find_one('task', {'task_id': 'test123'})

            # 验证 sanitizer 被调用
            mock_safe_find_one.assert_called_once()
            assert result == {"result": "test"}

    @patch('app.database.connection.MongoSanitizer.safe_find')
    def test_safe_find_calls_sanitizer(self, mock_safe_find):
        """测试 safe_find 调用 sanitizer"""
        mock_safe_find.return_value = [{"result": "test1"}, {"result": "test2"}]

        # 初始化 DatabaseManager
        with patch('app.database.connection.MongoClient') as mock_client:
            mock_client.return_value = MagicMock()
            DatabaseManager.init()

            # 调用 safe_find
            result = DatabaseManager.safe_find('task', {'status': 'pending'})

            # 验证 sanitizer 被调用
            mock_safe_find.assert_called_once()
            assert len(result) == 2

    @patch('app.database.connection.MongoSanitizer.safe_insert_one')
    def test_safe_insert_one_calls_sanitizer(self, mock_safe_insert_one):
        """测试 safe_insert_one 调用 sanitizer"""
        mock_safe_insert_one.return_value = True

        # 初始化 DatabaseManager
        with patch('app.database.connection.MongoClient') as mock_client:
            mock_client.return_value = MagicMock()
            DatabaseManager.init()

            # 调用 safe_insert_one
            result = DatabaseManager.safe_insert_one('task', {'task_id': 'test', 'target': 'example.com'})

            # 验证 sanitizer 被调用
            mock_safe_insert_one.assert_called_once()
            assert result is True

    @patch('app.database.connection.MongoSanitizer.safe_update_one')
    def test_safe_update_one_calls_sanitizer(self, mock_safe_update_one):
        """测试 safe_update_one 调用 sanitizer"""
        mock_safe_update_one.return_value = True

        # 初始化 DatabaseManager
        with patch('app.database.connection.MongoClient') as mock_client:
            mock_client.return_value = MagicMock()
            DatabaseManager.init()

            # 调用 safe_update_one
            result = DatabaseManager.safe_update_one(
                'task',
                {'task_id': 'test'},
                {'$set': {'status': 'completed'}}
            )

            # 验证 sanitizer 被调用
            mock_safe_update_one.assert_called_once()
            assert result is True

    @patch('app.database.connection.MongoSanitizer.safe_delete_one')
    def test_safe_delete_one_calls_sanitizer(self, mock_safe_delete_one):
        """测试 safe_delete_one 调用 sanitizer"""
        mock_safe_delete_one.return_value = True

        # 初始化 DatabaseManager
        with patch('app.database.connection.MongoClient') as mock_client:
            mock_client.return_value = MagicMock()
            DatabaseManager.init()

            # 调用 safe_delete_one
            result = DatabaseManager.safe_delete_one('task', {'task_id': 'test'})

            # 验证 sanitizer 被调用
            mock_safe_delete_one.assert_called_once()
            assert result is True


class TestNoSQLInjectionPrevention:
    """NoSQL 注入防护测试"""

    def test_dangerous_operators_removed(self):
        """测试危险操作符被移除"""
        # 模拟恶意查询
        malicious_query = {
            'username': 'admin',
            '$gt': '',  # 危险操作符
            '$ne': None,  # 危险操作符
            '$regex': '.*'  # 危险操作符
        }

        # 清理查询
        cleaned = MongoSanitizer.sanitize_query(malicious_query)

        # 验证危险操作符被移除
        assert '$gt' not in cleaned
        assert '$ne' not in cleaned
        assert '$regex' not in cleaned
        assert 'username' in cleaned

    def test_nested_dangerous_operators_removed(self):
        """测试嵌套危险操作符被移除"""
        malicious_query = {
            'status': 'active',
            '$or': [  # 危险操作符
                {'username': {'$gt': ''}},
                {'role': 'admin'}
            ]
        }

        # 清理查询
        cleaned = MongoSanitizer.sanitize_query(malicious_query)

        # 验证危险操作符被移除
        assert '$or' not in cleaned
        assert 'status' in cleaned

    def test_safe_values_preserved(self):
        """测试安全值被保留"""
        safe_query = {
            'task_id': 'task_123',
            'status': 'pending',
            'target': 'example.com',
            'count': 42,
            'enabled': True
        }

        # 清理查询
        cleaned = MongoSanitizer.sanitize_query(safe_query)

        # 验证安全值被保留
        assert cleaned == safe_query

    def test_string_sanitization(self):
        """测试字符串清理"""
        # 包含 null 字节和超长字符串
        dangerous_string = "hello\x00world" + "a" * 2000

        # 清理字符串
        cleaned = MongoSanitizer.sanitize_string(dangerous_string)

        # 验证 null 字节被移除，长度被限制
        assert '\x00' not in cleaned
        assert len(cleaned) <= 1000

    def test_objectid_sanitization(self):
        """测试 ObjectId 清理"""
        # 有效的 ObjectId
        valid_id = "507f1f77bcf86cd799439011"
        result = MongoSanitizer.sanitize_objectid(valid_id)
        assert result is not None

        # 无效的 ObjectId（包含危险字符）
        invalid_id = "507f1f77bcf86cd799439011'; DROP TABLE users; --"
        result = MongoSanitizer.sanitize_objectid(invalid_id)
        assert result is None

        # 非字符串
        result = MongoSanitizer.sanitize_objectid(12345)
        assert result is None
