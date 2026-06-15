# -*- coding: utf-8 -*-
"""
服务接口单元测试
"""

import pytest
from app.services.interfaces import (
    ServiceConfig,
    ServiceStatus,
    DnsServiceInterface,
    ScanServiceInterface,
    CacheServiceInterface
)


class TestServiceConfig:
    """测试 ServiceConfig 数据类"""

    def test_default_values(self):
        """测试默认值"""
        config = ServiceConfig(name="test-service")
        assert config.name == "test-service"
        assert config.host == "localhost"
        assert config.port == 0
        assert config.timeout == 30
        assert config.max_retries == 3

    def test_custom_values(self):
        """测试自定义值"""
        config = ServiceConfig(
            name="custom-service",
            host="192.168.1.100",
            port=8080,
            timeout=60,
            max_retries=5
        )
        assert config.name == "custom-service"
        assert config.host == "192.168.1.100"
        assert config.port == 8080
        assert config.timeout == 60
        assert config.max_retries == 5


class TestServiceStatus:
    """测试 ServiceStatus 数据类"""

    def test_running_status(self):
        """测试运行状态"""
        status = ServiceStatus(name="test-service", status="running", uptime=3600)
        assert status.name == "test-service"
        assert status.status == "running"
        assert status.uptime == 3600
        assert status.error is None

    def test_error_status(self):
        """测试错误状态"""
        status = ServiceStatus(
            name="test-service",
            status="error",
            uptime=0,
            error="Connection failed"
        )
        assert status.status == "error"
        assert status.error == "Connection failed"


class TestDnsServiceInterface:
    """测试 DnsServiceInterface 抽象类"""

    def test_is_abstract(self):
        """测试是抽象类"""
        with pytest.raises(TypeError):
            DnsServiceInterface()

    def test_implementation(self):
        """测试实现类"""
        class TestDnsService(DnsServiceInterface):
            def start(self): return True
            def stop(self): return True
            def restart(self): return True
            def get_status(self): return ServiceStatus("test", "running")
            def health_check(self): return True
            def query_a(self, domain): return []
            def query_cname(self, domain): return []
            def query_mx(self, domain): return []
            def query_ns(self, domain): return []
            def query_txt(self, domain): return []
            def batch_query(self, domains, record_type): return {}
            def clear_cache(self, domain=None): pass

        service = TestDnsService()
        assert service.health_check() is True


class TestScanServiceInterface:
    """测试 ScanServiceInterface 抽象类"""

    def test_is_abstract(self):
        """测试是抽象类"""
        with pytest.raises(TypeError):
            ScanServiceInterface()


class TestCacheServiceInterface:
    """测试 CacheServiceInterface 抽象类"""

    def test_is_abstract(self):
        """测试是抽象类"""
        with pytest.raises(TypeError):
            CacheServiceInterface()
