# -*- coding: utf-8 -*-
"""
RBAC权限系统测试
"""
import pytest
from unittest.mock import MagicMock, patch
from app.core.permissions import (
    Role,
    Permission,
    has_permission,
    has_role,
    require_permission,
    require_role,
    ROLE_PERMISSIONS,
    get_current_user_role,
)
from app.core.exceptions import AuthenticationException, AuthorizationException


class TestRole:
    def test_admin_role_value(self):
        assert Role.ADMIN.value == "admin"

    def test_operator_role_value(self):
        assert Role.OPERATOR.value == "operator"

    def test_viewer_role_value(self):
        assert Role.VIEWER.value == "viewer"

    def test_all_roles_have_permissions(self):
        for role in Role:
            assert len(ROLE_PERMISSIONS.get(role, set())) > 0


class TestPermission:
    def test_task_permission_values(self):
        assert Permission.TASK_CREATE.value == "task:create"
        assert Permission.TASK_READ.value == "task:read"
        assert Permission.TASK_DELETE.value == "task:delete"

    def test_user_permission_values(self):
        assert Permission.USER_CREATE.value == "user:create"
        assert Permission.USER_READ.value == "user:read"


class TestHasPermission:
    def test_admin_has_all_permissions(self):
        with patch('app.core.permissions.get_current_user_role', return_value=Role.ADMIN):
            for permission in Permission:
                assert has_permission(permission) is True

    def test_has_permission_without_user(self):
        with patch('app.core.permissions.get_current_user_role', return_value=None):
            assert has_permission(Permission.TASK_CREATE) is False


class TestHasRole:
    def test_has_role_admin(self):
        with patch('app.core.permissions.get_current_user_role', return_value=Role.ADMIN):
            assert has_role(Role.ADMIN) is True
            assert has_role(Role.OPERATOR) is False

    def test_has_role_viewer(self):
        with patch('app.core.permissions.get_current_user_role', return_value=Role.VIEWER):
            assert has_role(Role.VIEWER) is True
            assert has_role(Role.ADMIN) is False


class TestRequirePermission:
    def test_decorator_preserves_function_metadata(self):
        @require_permission(Permission.TASK_READ)
        def my_function():
            """我的文档字符串"""
            pass

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "我的文档字符串"


class TestRequireRole:
    def test_decorator_preserves_function_metadata(self):
        @require_role(Role.ADMIN)
        def my_function():
            """我的文档字符串"""
            pass

        assert my_function.__name__ == "my_function"
        assert my_function.__doc__ == "我的文档字符串"


class TestRolePermissionMapping:
    def test_admin_can_manage_users(self):
        assert Permission.USER_CREATE in ROLE_PERMISSIONS[Role.ADMIN]
        assert Permission.USER_READ in ROLE_PERMISSIONS[Role.ADMIN]

    def test_operator_permissions(self):
        assert Permission.TASK_CREATE in ROLE_PERMISSIONS[Role.OPERATOR]
        assert Permission.TASK_READ in ROLE_PERMISSIONS[Role.OPERATOR]

    def test_viewer_read_only(self):
        viewer_permissions = ROLE_PERMISSIONS[Role.VIEWER]
        assert Permission.TASK_READ in viewer_permissions
        assert len(viewer_permissions) >= 1
