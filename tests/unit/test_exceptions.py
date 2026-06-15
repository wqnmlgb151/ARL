# -*- coding: utf-8 -*-
"""
异常类结构测试
"""
import pytest
from app.core.exceptions import (
    ARLException,
    DatabaseException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    RateLimitException,
)


class TestARLException:
    """基础异常测试"""

    def test_default_values(self):
        exc = ARLException("test error")
        assert exc.message == "test error"
        assert exc.code == "INTERNAL_ERROR"
        assert exc.details == {}

    def test_with_code(self):
        exc = ARLException("test error", code="TEST_ERROR")
        assert exc.code == "TEST_ERROR"

    def test_with_details(self):
        exc = ARLException("test error", details={"key": "value"})
        assert exc.details == {"key": "value"}

    def test_to_dict(self):
        exc = ARLException(
            "test error",
            code="TEST_ERROR",
            details={"key": "value"}
        )
        result = exc.to_dict()
        assert result["message"] == "test error"
        assert result["code"] == "TEST_ERROR"
        assert result["details"] == {"key": "value"}

    def test_str_representation(self):
        exc = ARLException("test error", code="TEST_ERROR")
        assert "test error" in str(exc)


class TestDatabaseException:
    """数据库异常测试"""

    def test_default_values(self):
        exc = DatabaseException("db error")
        assert exc.message == "db error"
        assert exc.code == "DATABASE_ERROR"

    def test_with_details(self):
        exc = DatabaseException("db error", details={"collection": "users"})
        assert exc.details["collection"] == "users"


class TestValidationException:
    """验证异常测试"""

    def test_default_values(self):
        exc = ValidationException("validation error")
        assert exc.message == "validation error"
        assert exc.code == "VALIDATION_ERROR"

    def test_with_field(self):
        exc = ValidationException("validation error", field="username")
        assert exc.details["field"] == "username"

    def test_with_field_and_details(self):
        exc = ValidationException("validation error", field="age", details={"value": "abc"})
        assert exc.details["field"] == "age"
        assert exc.details["value"] == "abc"


class TestAuthenticationException:
    """认证异常测试"""

    def test_default_values(self):
        exc = AuthenticationException("auth error")
        assert exc.message == "auth error"
        assert exc.code == "AUTHENTICATION_ERROR"

    def test_invalid_api_key(self):
        exc = AuthenticationException("Invalid API key")
        assert "API" in str(exc)


class TestAuthorizationException:
    """授权异常测试"""

    def test_default_values(self):
        exc = AuthorizationException("forbidden")
        assert exc.message == "forbidden"
        assert exc.code == "AUTHORIZATION_ERROR"

    def test_with_details(self):
        exc = AuthorizationException("forbidden", details={"permission": "admin"})
        assert exc.details["permission"] == "admin"


class TestNotFoundException:
    """未找到异常测试"""

    def test_default_values(self):
        exc = NotFoundException("not found")
        assert exc.message == "not found"
        assert exc.code == "NOT_FOUND"

    def test_with_resource_type(self):
        exc = NotFoundException("user not found", resource_type="user")
        assert exc.details["resource_type"] == "user"

    def test_with_details(self):
        exc = NotFoundException("user not found", resource_type="user", details={"resource_id": "123"})
        assert exc.details["resource_type"] == "user"
        assert exc.details["resource_id"] == "123"


class TestRateLimitException:
    """速率限制异常测试"""

    def test_default_values(self):
        exc = RateLimitException("rate limit exceeded")
        assert exc.message == "rate limit exceeded"
        assert exc.code == "RATE_LIMIT_ERROR"

    def test_with_retry_after(self):
        exc = RateLimitException("rate limit exceeded", retry_after=60)
        assert exc.details["retry_after"] == 60


class TestExceptionHierarchy:
    """异常继承关系测试"""

    def test_all_exceptions_inherit_from_base(self):
        assert issubclass(DatabaseException, ARLException)
        assert issubclass(ValidationException, ARLException)
        assert issubclass(AuthenticationException, ARLException)
        assert issubclass(AuthorizationException, ARLException)
        assert issubclass(NotFoundException, ARLException)
        assert issubclass(RateLimitException, ARLException)

    def test_exception_catch_order(self):
        with pytest.raises(ARLException):
            raise DatabaseException("test")

        with pytest.raises(ARLException):
            raise ValidationException("test")
