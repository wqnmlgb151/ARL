# -*- coding: utf-8 -*-
"""
缓存服务单元测试
"""

import pytest
from unittest.mock import patch, MagicMock

from app.services.cache_service import CacheService


class TestCacheService:
    """测试 CacheService 类"""

    def test_get(self):
        """测试获取缓存"""
        with patch('app.services.cache_service.redis_manager') as mock_manager:
            mock_manager.get.return_value = {"test": "data"}

            result = CacheService.get("test_key")

            assert result == {"test": "data"}
            mock_manager.get.assert_called_once_with("test_key")

    def test_set(self):
        """测试设置缓存"""
        with patch('app.services.cache_service.redis_manager') as mock_manager:
            mock_manager.set.return_value = True

            result = CacheService.set("test_key", "value", 3600)

            assert result is True
            mock_manager.set.assert_called_once_with("test_key", "value", 3600)

    def test_delete(self):
        """测试删除缓存"""
        with patch('app.services.cache_service.redis_manager') as mock_manager:
            mock_manager.delete.return_value = True

            result = CacheService.delete("test_key")

            assert result is True
            mock_manager.delete.assert_called_once_with("test_key")

    def test_exists(self):
        """测试检查存在"""
        with patch('app.services.cache_service.redis_manager') as mock_manager:
            mock_manager.exists.return_value = True

            result = CacheService.exists("test_key")

            assert result is True
            mock_manager.exists.assert_called_once_with("test_key")

    def test_cache_dns_result(self):
        """测试缓存 DNS 结果"""
        with patch('app.services.cache_service.redis_manager') as mock_manager:
            mock_manager.set.return_value = True

            result = CacheService.cache_dns_result("example.com", "A", ["1.2.3.4"])

            assert result is True
            mock_manager.set.assert_called_once()
            call_args = mock_manager.set.call_args
            assert "dns:A:example.com" in call_args[0][0]

    def test_get_dns_result(self):
        """测试获取 DNS 缓存"""
        with patch('app.services.cache_service.redis_manager') as mock_manager:
            mock_manager.get.return_value = ["1.2.3.4"]

            result = CacheService.get_dns_result("example.com", "A")

            assert result == ["1.2.3.4"]
            mock_manager.get.assert_called_once()

    def test_cache_scan_result(self):
        """测试缓存扫描结果"""
        with patch('app.services.cache_service.redis_manager') as mock_manager:
            mock_manager.set.return_value = True

            result = CacheService.cache_scan_result("192.168.1.1", {"ports": [80, 443]})

            assert result is True
            mock_manager.set.assert_called_once()

    def test_cache_session(self):
        """测试缓存会话"""
        with patch('app.services.cache_service.redis_manager') as mock_manager:
            mock_manager.set.return_value = True

            result = CacheService.cache_session("session123", {"user": "admin"})

            assert result is True
            mock_manager.set.assert_called_once()

    def test_delete_session(self):
        """测试删除会话"""
        with patch('app.services.cache_service.redis_manager') as mock_manager:
            mock_manager.delete.return_value = True

            result = CacheService.delete_session("session123")

            assert result is True
            mock_manager.delete.assert_called_once()

    def test_cache_task_status(self):
        """测试缓存任务状态"""
        with patch('app.services.cache_service.redis_manager') as mock_manager:
            mock_manager.set.return_value = True

            result = CacheService.cache_task_status("task123", {"status": "running"})

            assert result is True
            mock_manager.set.assert_called_once()

    def test_clear_prefix(self):
        """测试清除前缀"""
        with patch('app.services.cache_service.redis_manager') as mock_manager:
            mock_manager.clear_pattern.return_value = 10

            result = CacheService.clear_prefix("dns")

            assert result == 10
            mock_manager.clear_pattern.assert_called_once_with("dns:*")

    def test_clear_all(self):
        """测试清除所有"""
        with patch('app.services.cache_service.redis_manager') as mock_manager:
            mock_manager.clear_pattern.return_value = 100

            result = CacheService.clear_all()

            assert result == 100
            mock_manager.clear_pattern.assert_called_once_with("*")

    def test_get_stats(self):
        """测试获取统计"""
        with patch('app.services.cache_service.redis_manager') as mock_manager:
            mock_manager.get_stats.return_value = {"enabled": True, "total_keys": 50}

            result = CacheService.get_stats()

            assert result["enabled"] is True
            assert result["total_keys"] == 50

    def test_is_enabled(self):
        """测试是否启用"""
        with patch('app.services.cache_service.redis_manager') as mock_manager:
            mock_manager.enabled = True

            result = CacheService.is_enabled()

            assert result is True
