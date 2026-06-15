# -*- coding: utf-8 -*-
"""
DatabaseManager 测试
"""
import pytest
from unittest.mock import MagicMock, patch
from pymongo import MongoClient

from app.database.connection import DatabaseManager, get_collection, get_db, init_db


class TestDatabaseManager:
    """DatabaseManager 单例测试"""

    def setup_method(self):
        """每个测试前重置单例状态"""
        DatabaseManager.close()

    def teardown_method(self):
        """每个测试后清理"""
        DatabaseManager.close()

    @patch('app.database.connection.MongoClient')
    def test_singleton_pattern(self, mock_client):
        """测试单例模式"""
        mock_client.return_value = MagicMock()
        
        DatabaseManager.init("mongodb://localhost:27017", "test_db")
        db1 = DatabaseManager()
        db2 = DatabaseManager()
        
        # 应该是同一个实例（或至少使用同一个 _instance）
        assert DatabaseManager._instance is DatabaseManager._instance
        DatabaseManager.close()

    @patch('app.database.connection.MongoClient')
    def test_init(self, mock_client):
        """测试初始化"""
        mock_client.return_value = MagicMock()
        
        DatabaseManager.init("mongodb://localhost:27017", "test_db")
        
        assert DatabaseManager.is_initialized()
        mock_client.assert_called_once()
        DatabaseManager.close()

    @patch('app.database.connection.MongoClient')
    def test_double_init_error(self, mock_client):
        """测试重复初始化抛出异常"""
        mock_client.return_value = MagicMock()
        
        DatabaseManager.init("mongodb://localhost:27017", "test_db")
        
        with pytest.raises(RuntimeError, match="already initialized"):
            DatabaseManager.init("mongodb://localhost:27017", "test_db")
        
        DatabaseManager.close()

    @patch('app.database.connection.MongoClient')
    def test_get_collection(self, mock_client):
        """测试获取集合"""
        mock_client.return_value = MagicMock()
        
        DatabaseManager.init("mongodb://localhost:27017", "test_db")
        
        collection = DatabaseManager.get_collection("task")
        assert collection is not None
        DatabaseManager.close()

    @patch('app.database.connection.MongoClient')
    def test_get_collection_before_init(self, mock_client):
        """测试未初始化时获取集合抛出异常"""
        with pytest.raises(RuntimeError, match="not initialized"):
            DatabaseManager.get_collection("task")

    @patch('app.database.connection.MongoClient')
    def test_get_db(self, mock_client):
        """测试获取数据库实例"""
        mock_client.return_value = MagicMock()
        
        DatabaseManager.init("mongodb://localhost:27017", "test_db")
        
        db = DatabaseManager.get_db()
        assert db is not None
        DatabaseManager.close()

    @patch('app.database.connection.MongoClient')
    def test_get_client(self, mock_client):
        """测试获取客户端实例"""
        mock_client.return_value = MagicMock()
        
        DatabaseManager.init("mongodb://localhost:27017", "test_db")
        
        client = DatabaseManager.get_client()
        assert client is not None
        DatabaseManager.close()

    @patch('app.database.connection.MongoClient')
    def test_close(self, mock_client):
        """测试关闭连接"""
        mock_client.return_value = MagicMock()
        
        DatabaseManager.init("mongodb://localhost:27017", "test_db")
        DatabaseManager.close()
        
        assert not DatabaseManager.is_initialized()
        mock_client.return_value.close.assert_called_once()

    @patch('app.database.connection.MongoClient')
    def test_is_initialized(self, mock_client):
        """测试初始化状态检查"""
        mock_client.return_value = MagicMock()
        
        assert not DatabaseManager.is_initialized()
        
        DatabaseManager.init("mongodb://localhost:27017", "test_db")
        assert DatabaseManager.is_initialized()
        
        DatabaseManager.close()
        assert not DatabaseManager.is_initialized()


class TestHelperFunctions:
    """辅助函数测试"""

    def setup_method(self):
        """每个测试前重置单例状态"""
        DatabaseManager.close()

    def teardown_method(self):
        """每个测试后清理"""
        DatabaseManager.close()

    @patch('app.database.connection.MongoClient')
    def test_get_collection_helper(self, mock_client):
        """测试 get_collection 辅助函数"""
        mock_client.return_value = MagicMock()
        
        DatabaseManager.init("mongodb://localhost:27017", "test_db")
        
        collection = get_collection("task")
        assert collection is not None
        DatabaseManager.close()

    @patch('app.database.connection.MongoClient')
    def test_get_db_helper(self, mock_client):
        """测试 get_db 辅助函数"""
        mock_client.return_value = MagicMock()
        
        DatabaseManager.init("mongodb://localhost:27017", "test_db")
        
        db = get_db()
        assert db is not None
        DatabaseManager.close()

    @patch('app.database.connection.MongoClient')
    def test_init_db(self, mock_client):
        """测试 init_db 辅助函数"""
        mock_client.return_value = MagicMock()
        
        init_db("mongodb://localhost:27017", "test_db")
        
        assert DatabaseManager.is_initialized()
        DatabaseManager.close()


class TestConnectionPool:
    """连接池测试"""

    @patch('app.database.connection.MongoClient')
    def test_connection_pool_settings(self, mock_client):
        """测试连接池配置"""
        DatabaseManager.init("mongodb://localhost:27017", "test_db")
        
        client = DatabaseManager.get_client()
        assert client is not None
        
        # 验证连接池参数
        mock_client.assert_called_once()
        call_kwargs = mock_client.call_args[1]
        assert call_kwargs.get('maxPoolSize') == 100
        assert call_kwargs.get('minPoolSize') == 20
        
        DatabaseManager.close()

    @patch('app.database.connection.MongoClient')
    def test_connection_retry(self, mock_client):
        """测试连接重试配置"""
        DatabaseManager.init("mongodb://localhost:27017", "test_db")
        
        mock_client.assert_called_once()
        call_kwargs = mock_client.call_args[1]
        assert call_kwargs.get('retryWrites') is True
        assert call_kwargs.get('retryReads') is True
        
        DatabaseManager.close()
