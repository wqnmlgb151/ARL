# -*- coding: utf-8 -*-
"""
ARL统一异常定义
提供层次化的异常体系，便于错误处理和日志记录
"""

from typing import Any, Dict, Optional


class ARLException(Exception):
    """
    ARL基础异常类

    所有自定义异常都应继承此类，便于统一捕获和处理

    Attributes:
        message: 错误消息
        code: 错误代码（用于API响应）
        details: 额外错误详情
    """

    def __init__(self, message: str, code: str = "INTERNAL_ERROR", details: Optional[Dict[str, Any]] = None):
        self.message = message
        self.code = code
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式（用于API响应）"""
        return {
            'error': True,
            'code': self.code,
            'message': self.message,
            'details': self.details
        }


class DatabaseException(ARLException):
    """数据库操作异常"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="DATABASE_ERROR", details=details)


class ValidationException(ARLException):
    """数据验证异常"""

    def __init__(self, message: str, field: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        if field:
            details = details or {}
            details['field'] = field
        super().__init__(message, code="VALIDATION_ERROR", details=details)


class AuthenticationException(ARLException):
    """认证异常"""

    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="AUTHENTICATION_ERROR", details=details)


class AuthorizationException(ARLException):
    """授权异常"""

    def __init__(self, message: str = "Permission denied", details: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="AUTHORIZATION_ERROR", details=details)


class NotFoundException(ARLException):
    """资源未找到异常"""

    def __init__(self, message: str = "Resource not found", resource_type: Optional[str] = None,
                 details: Optional[Dict[str, Any]] = None):
        if resource_type:
            details = details or {}
            details['resource_type'] = resource_type
        super().__init__(message, code="NOT_FOUND", details=details)


class RateLimitException(ARLException):
    """速率限制异常"""

    def __init__(self, message: str = "Rate limit exceeded", retry_after: Optional[int] = None,
                 details: Optional[Dict[str, Any]] = None):
        if retry_after:
            details = details or {}
            details['retry_after'] = retry_after
        super().__init__(message, code="RATE_LIMIT_ERROR", details=details)


class ExternalServiceException(ARLException):
    """外部服务异常"""

    def __init__(self, service: str, message: str, details: Optional[Dict[str, Any]] = None):
        details = details or {}
        details['service'] = service
        super().__init__(f"{service}: {message}", code="EXTERNAL_SERVICE_ERROR", details=details)


class ConfigurationException(ARLException):
    """配置异常"""

    def __init__(self, message: str, config_key: Optional[str] = None, details: Optional[Dict[str, Any]] = None):
        if config_key:
            details = details or {}
            details['config_key'] = config_key
        super().__init__(message, code="CONFIGURATION_ERROR", details=details)
