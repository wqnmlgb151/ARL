# -*- coding: utf-8 -*-
"""
Redis 工具模块单元测试
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json

# 模拟 redis 模块
mock_redis = MagicMock()
mock_redis.Redis = MagicMock()
mock_redis.ConnectionPool = MagicMock()
mock_redis.ConnectionError = Exception

with patch.dict('sys.modules', {'redis': mock_redis}):
    from app.utils.redis_utils import RedisManager, cache_result, invalidate_cache


class TestRedisManager:
    """测试 RedisManager 类"""

    def test_init(self):
        """测试初始化"""
        manager = RedisManager()
        assert manager._pool is None
        assert manager._client is None
        assert manager._enabled is False

    def test_init_app_success(self):
        """测试成功初始化"""
        manager = RedisManager()
        mock_client = MagicMock()
        mock_redis.Redis.return_value = mock_client
        mock_client.ping.return_value = True

        config = {
            'REDIS_HOST': 'localhost',
            'REDIS_PORT': 6379,
            'REDIS_DB': 0,
            'REDIS_PASSWORD': None
        }

        manager.init_app(config)

        assert manager._enabled is True
        assert manager._client is not None

    def test_init_app_connection_error(self):
        """测试连接失败"""
        manager = RedisManager()
        mock_client = MagicMock()
        mock_redis.Redis.return_value = mock_client
        mock_client.ping.side_effect = Exception("Connection refused")

        config = {
            'REDIS_HOST': 'localhost',
            'REDIS_PORT': 6379,
            'REDIS_DB': 0,
            'REDIS_PASSWORD': None
        }

        manager.init_app(config)

        assert manager._enabled is False

    def test_enabled_property(self):
        """测试 enabled 属性"""
        manager = RedisManager()
        assert manager.enabled is False

        manager._enabled = True
        manager._client = MagicMock()
        assert manager.enabled is True

    def test_get_when_disabled(self):
        """测试禁用时获取"""
        manager = RedisManager()
        result = manager.get("test_key")
        assert result is None

    def test_set_when_disabled(self):
        """测试禁用时设置"""
        manager = RedisManager()
        result = manager.set("test_key", "value")
        assert result is False

    def test_delete_when_disabled(self):
        """测试禁用时删除"""
        manager = RedisManager()
        result = manager.delete("test_key")
        assert result is False

    def test_exists_when_disabled(self):
        """测试禁用时检查存在"""
        manager = RedisManager()
        result = manager.exists("test_key")
        assert result is False

    def test_clear_pattern_when_disabled(self):
        """测试禁用时清除模式"""
        manager = RedisManager()
        result = manager.clear_pattern("test:*")
        assert result == 0

    def test_get_stats_when_disabled(self):
        """测试禁用时获取统计"""
        manager = RedisManager()
        stats = manager.get_stats()
        assert stats["enabled"] is False

    def test_close(self):
        """测试关闭连接"""
        manager = RedisManager()
        mock_pool = MagicMock()
        manager._pool = mock_pool

        manager.close()

        mock_pool.disconnect.assert_called_once()


class TestCacheResultDecorator:
    """测试 cache_result 装饰器"""

    def test_cache_miss(self):
        """测试缓存未命中"""
        mock_manager = MagicMock()
        mock_manager.get.return_value = None
        mock_manager.set.return_value = True

        with patch('app.utils.redis_utils.redis_manager', mock_manager):
            @cache_result(ttl=3600, key_prefix="test")
            def test_func(x, y):
                return x + y

            result = test_func(1, 2)

            assert result == 3
            mock_manager.get.assert_called_once()
            mock_manager.set.assert_called_once()

    def test_cache_hit(self):
        """测试缓存命中"""
        mock_manager = MagicMock()
        mock_manager.get.return_value = 42

        with patch('app.utils.redis_utils.redis_manager', mock_manager):
            @cache_result(ttl=3600, key_prefix="test")
            def test_func(x, y):
                return x + y

            result = test_func(1, 2)

            assert result == 42
            mock_manager.get.assert_called_once()
            mock_manager.set.assert_not_called()

    def test_cache_disabled(self):
        """测试缓存禁用"""
        mock_manager = MagicMock()
        mock_manager.get.return_value = None
        mock_manager.enabled = False

        with patch('app.utils.redis_utils.redis_manager', mock_manager):
            @cache_result(ttl=3600, key_prefix="test")
            def test_func(x, y):
                return x + y

            result = test_func(1, 2)

            assert result == 3


class TestInvalidateCache:
    """测试 invalidate_cache 函数"""

    def test_invalidate_specific_key(self):
        """测试使特定键失效"""
        mock_manager = MagicMock()

        with patch('app.utils.redis_utils.redis_manager', mock_manager):
            invalidate_cache("test", "arg1", key="value")

            mock_manager.delete.assert_called_once()

    def test_invalidate_pattern(self):
        """测试使模式失效"""
        mock_manager = MagicMock()

        with patch('app.utils.redis_utils.redis_manager', mock_manager):
            invalidate_cache("test")

            mock_manager.clear_pattern.assert_called_once_with("test:*")
