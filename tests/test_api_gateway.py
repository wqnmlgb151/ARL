# -*- coding: utf-8 -*-
"""
API 网关单元测试
"""

import pytest
import json
from unittest.mock import patch, MagicMock

from app.api.gateway import (
    ApiGateway,
    RequestContext,
    ResponseBuilder,
    RateLimitConfig,
    AuthConfig,
    require_api_key
)


class TestRequestContext:
    """测试 RequestContext 数据类"""

    def test_creation(self):
        """测试创建"""
        context = RequestContext(
            request_id="test-123",
            method="GET",
            path="/api/test",
            headers={"Content-Type": "application/json"},
            params={"key": "value"},
            body={"data": "test"}
        )

        assert context.request_id == "test-123"
        assert context.method == "GET"
        assert context.path == "/api/test"
        assert context.headers["Content-Type"] == "application/json"
        assert context.params["key"] == "value"
        assert context.body["data"] == "test"

    def test_elapsed_time(self):
        """测试耗时计算"""
        import time
        context = RequestContext(
            request_id="test",
            method="GET",
            path="/api/test",
            headers={},
            params={},
            body=None,
            start_time=time.time() - 1
        )

        elapsed = context.elapsed_time()
        assert elapsed >= 0.9


class TestResponseBuilder:
    """测试 ResponseBuilder 类"""

    def test_success_response(self):
        """测试成功响应"""
        response = ResponseBuilder.success(data={"key": "value"})

        assert response["code"] == 200
        assert response["message"] == "success"
        assert response["data"]["key"] == "value"
        assert response["success"] is True

    def test_error_response(self):
        """测试错误响应"""
        response = ResponseBuilder.error("Test error", code=400)

        assert response["code"] == 400
        assert response["message"] == "Test error"
        assert response["success"] is False

    def test_unauthorized_response(self):
        """测试未授权响应"""
        response = ResponseBuilder.unauthorized()

        assert response["code"] == 401
        assert response["success"] is False

    def test_forbidden_response(self):
        """测试禁止访问响应"""
        response = ResponseBuilder.forbidden()

        assert response["code"] == 403
        assert response["success"] is False

    def test_not_found_response(self):
        """测试未找到响应"""
        response = ResponseBuilder.not_found()

        assert response["code"] == 404
        assert response["success"] is False

    def test_too_many_requests_response(self):
        """测试限流响应"""
        response = ResponseBuilder.too_many_requests()

        assert response["code"] == 429
        assert response["success"] is False

    def test_internal_error_response(self):
        """测试服务器错误响应"""
        response = ResponseBuilder.internal_error()

        assert response["code"] == 500
        assert response["success"] is False


class TestApiGateway:
    """测试 ApiGateway 类"""

    def test_init(self):
        """测试初始化"""
        gateway = ApiGateway()
        assert gateway.app is None
        assert gateway.rate_limit_config.enabled is True
        assert gateway.auth_config.enabled is True

    def test_init_app(self):
        """测试初始化应用"""
        from flask import Flask
        app = Flask(__name__)
        gateway = ApiGateway(app)

        assert gateway.app is app

    def test_add_middleware(self):
        """测试添加中间件"""
        gateway = ApiGateway()

        def test_middleware(context):
            return None

        gateway.add_middleware(test_middleware)
        assert len(gateway._middleware) == 1

    def test_set_rate_limit(self):
        """测试设置限流配置"""
        gateway = ApiGateway()
        config = RateLimitConfig(enabled=False)
        gateway.set_rate_limit(config)

        assert gateway.rate_limit_config.enabled is False

    def test_set_auth(self):
        """测试设置认证配置"""
        gateway = ApiGateway()
        config = AuthConfig(enabled=False)
        gateway.set_auth(config)

        assert gateway.auth_config.enabled is False


class TestRateLimitConfig:
    """测试 RateLimitConfig 数据类"""

    def test_default_values(self):
        """测试默认值"""
        config = RateLimitConfig()
        assert config.enabled is True
        assert config.requests_per_minute == 60
        assert config.burst_size == 10

    def test_custom_values(self):
        """测试自定义值"""
        config = RateLimitConfig(
            enabled=True,
            requests_per_minute=100,
            burst_size=20
        )
        assert config.requests_per_minute == 100
        assert config.burst_size == 20


class TestAuthConfig:
    """测试 AuthConfig 数据类"""

    def test_default_values(self):
        """测试默认值"""
        config = AuthConfig()
        assert config.enabled is True
        assert config.api_key_header == "Token"
        assert "/api/doc" in config.excluded_paths

    def test_custom_values(self):
        """测试自定义值"""
        config = AuthConfig(
            enabled=True,
            api_key_header="X-API-Key",
            excluded_paths=["/health", "/metrics"]
        )
        assert config.api_key_header == "X-API-Key"
        assert "/health" in config.excluded_paths
