# -*- coding: utf-8 -*-
"""
ARL核心模块
包含异常定义、类型定义、验证器和权限控制
"""

from app.core.exceptions import (
    ARLException,
    DatabaseException,
    ValidationException,
    AuthenticationException,
    AuthorizationException,
    NotFoundException,
    RateLimitException
)
from app.core.types import TaskInfo, DomainInfo, IPInfo, SiteInfo, UserInfo, ScanResult
from app.core.validators import validate_ip, validate_domain, validate_url, validate_port, sanitize_input
from app.core.permissions import Role, Permission, require_permission, require_role
from app.core.audit import AuditLog, audit_log

__all__ = [
    # 异常
    'ARLException',
    'DatabaseException',
    'ValidationException',
    'AuthenticationException',
    'AuthorizationException',
    'NotFoundException',
    'RateLimitException',
    # 类型
    'TaskInfo',
    'DomainInfo',
    'IPInfo',
    'SiteInfo',
    'UserInfo',
    'ScanResult',
    # 验证器
    'validate_ip',
    'validate_domain',
    'validate_url',
    'validate_port',
    'sanitize_input',
    # 权限
    'Role',
    'Permission',
    'require_permission',
    'require_role',
    # 审计
    'AuditLog',
    'audit_log'
]
