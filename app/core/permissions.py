# -*- coding: utf-8 -*-
"""
ARL权限控制模块
实现基于角色的访问控制（RBAC）
"""

import functools
import logging
from enum import Enum
from typing import Callable, List, Optional, Set

from flask import request, g

from app.core.exceptions import AuthenticationException, AuthorizationException

logger = logging.getLogger(__name__)


class Role(Enum):
    """用户角色枚举"""
    ADMIN = "admin"  # 管理员：所有权限
    OPERATOR = "operator"  # 操作员：任务管理权限
    AUDITOR = "auditor"  # 审计员：查看和审计权限
    VIEWER = "viewer"  # 查看者：只读权限


class Permission(Enum):
    """权限枚举"""
    # 任务权限
    TASK_CREATE = "task:create"
    TASK_READ = "task:read"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"
    TASK_CANCEL = "task:cancel"

    # 资产权限
    DOMAIN_READ = "domain:read"
    IP_READ = "ip:read"
    SITE_READ = "site:read"
    URL_READ = "url:read"
    CERT_READ = "cert:read"

    # 调度器权限
    SCHEDULER_CREATE = "scheduler:create"
    SCHEDULER_READ = "scheduler:read"
    SCHEDULER_UPDATE = "scheduler:update"
    SCHEDULER_DELETE = "scheduler:delete"

    # 用户权限
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"

    # 系统权限
    SYSTEM_CONFIG = "system:config"
    SYSTEM_LOG = "system:log"
    SYSTEM_AUDIT = "system:audit"
    SYSTEM_EXPORT = "system:export"


# 角色-权限映射
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        # 管理员拥有所有权限
        Permission.TASK_CREATE, Permission.TASK_READ, Permission.TASK_UPDATE, Permission.TASK_DELETE, Permission.TASK_CANCEL,
        Permission.DOMAIN_READ, Permission.IP_READ, Permission.SITE_READ, Permission.URL_READ, Permission.CERT_READ,
        Permission.SCHEDULER_CREATE, Permission.SCHEDULER_READ, Permission.SCHEDULER_UPDATE, Permission.SCHEDULER_DELETE,
        Permission.USER_CREATE, Permission.USER_READ, Permission.USER_UPDATE, Permission.USER_DELETE,
        Permission.SYSTEM_CONFIG, Permission.SYSTEM_LOG, Permission.SYSTEM_AUDIT, Permission.SYSTEM_EXPORT
    },
    Role.OPERATOR: {
        # 操作员可以管理任务
        Permission.TASK_CREATE, Permission.TASK_READ, Permission.TASK_UPDATE, Permission.TASK_CANCEL,
        Permission.DOMAIN_READ, Permission.IP_READ, Permission.SITE_READ, Permission.URL_READ, Permission.CERT_READ,
        Permission.SCHEDULER_READ,
        Permission.SYSTEM_EXPORT
    },
    Role.AUDITOR: {
        # 审计员可以查看所有内容
        Permission.TASK_READ,
        Permission.DOMAIN_READ, Permission.IP_READ, Permission.SITE_READ, Permission.URL_READ, Permission.CERT_READ,
        Permission.SCHEDULER_READ,
        Permission.USER_READ,
        Permission.SYSTEM_LOG, Permission.SYSTEM_AUDIT, Permission.SYSTEM_EXPORT
    },
    Role.VIEWER: {
        # 查看者只能查看
        Permission.TASK_READ,
        Permission.DOMAIN_READ, Permission.IP_READ, Permission.SITE_READ, Permission.URL_READ, Permission.CERT_READ,
        Permission.SCHEDULER_READ
    }
}


def get_current_user_role() -> Optional[Role]:
    """
    获取当前用户的角色

    Returns:
        用户角色，未认证返回None
    """
    user = getattr(g, 'current_user', None)
    if not user:
        return None

    role_str = user.get('role', 'viewer')
    try:
        return Role(role_str)
    except ValueError:
        logger.warning(f"Invalid role: {role_str}, defaulting to viewer")
        return Role.VIEWER


def has_permission(permission: Permission) -> bool:
    """
    检查当前用户是否拥有指定权限

    Args:
        permission: 要检查的权限

    Returns:
        是否拥有权限
    """
    role = get_current_user_role()
    if not role:
        return False

    return permission in ROLE_PERMISSIONS.get(role, set())


def has_role(role: Role) -> bool:
    """
    检查当前用户是否拥有指定角色

    Args:
        role: 要检查的角色

    Returns:
        是否拥有角色
    """
    current_role = get_current_user_role()
    if not current_role:
        return False

    return current_role == role


def require_permission(permission: Permission) -> Callable:
    """
    权限检查装饰器

    用法：
        @require_permission(Permission.TASK_CREATE)
        def create_task():
            ...

    Args:
        permission: 需要的权限

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 检查认证
            user = getattr(g, 'current_user', None)
            if not user:
                raise AuthenticationException("Authentication required")

            # 检查权限
            if not has_permission(permission):
                logger.warning(
                    f"Permission denied: user={user.get('username')}, "
                    f"required={permission.value}"
                )
                raise AuthorizationException(
                    f"Permission denied: {permission.value} required",
                    details={'required_permission': permission.value}
                )

            return func(*args, **kwargs)

        return wrapper
    return decorator


def require_role(role: Role) -> Callable:
    """
    角色检查装饰器

    用法：
        @require_role(Role.ADMIN)
        def admin_only():
            ...

    Args:
        role: 需要的角色

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 检查认证
            user = getattr(g, 'current_user', None)
            if not user:
                raise AuthenticationException("Authentication required")

            # 检查角色
            user_role = get_current_user_role()
            if user_role != role:
                logger.warning(
                    f"Role denied: user={user.get('username')}, "
                    f"user_role={user_role}, required={role.value}"
                )
                raise AuthorizationException(
                    f"Role denied: {role.value} required",
                    details={'required_role': role.value}
                )

            return func(*args, **kwargs)

        return wrapper
    return decorator


def require_any_role(roles: List[Role]) -> Callable:
    """
    多角色检查装饰器（满足其一即可）

    用法：
        @require_any_role([Role.ADMIN, Role.OPERATOR])
        def multi_role():
            ...

    Args:
        roles: 角色列表

    Returns:
        装饰器函数
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # 检查认证
            user = getattr(g, 'current_user', None)
            if not user:
                raise AuthenticationException("Authentication required")

            # 检查角色
            user_role = get_current_user_role()
            if user_role not in roles:
                logger.warning(
                    f"Role denied: user={user.get('username')}, "
                    f"user_role={user_role}, required={[r.value for r in roles]}"
                )
                raise AuthorizationException(
                    f"Role denied: one of {[r.value for r in roles]} required",
                    details={'required_roles': [r.value for r in roles]}
                )

            return func(*args, **kwargs)

        return wrapper
    return decorator


def check_api_key() -> bool:
    """
    检查API Key认证

    Returns:
        认证是否通过
    """
    from app.database.repositories import UserRepository

    api_key = request.headers.get('X-API-Key')
    if not api_key:
        return False

    user_repo = UserRepository()
    user = user_repo.find_by_api_key(api_key)
    if not user:
        return False

    # 设置当前用户
    g.current_user = {
        'username': user['username'],
        'role': user.get('role', 'viewer'),
        'id': str(user.get('_id', ''))
    }

    return True


# 导出
__all__ = [
    'Role',
    'Permission',
    'ROLE_PERMISSIONS',
    'get_current_user_role',
    'has_permission',
    'require_permission',
    'require_role',
    'require_any_role',
    'check_api_key'
]
