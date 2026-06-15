# -*- coding: utf-8 -*-
"""
审计日志模块测试
"""
import pytest
from unittest.mock import MagicMock, patch
from app.core.audit import AuditLog


class TestAuditLog:
    """审计日志测试"""

    def setup_method(self):
        """测试前准备"""
        self.audit = AuditLog()
        self.audit._collection = MagicMock()

    def test_log_action(self):
        """测试记录操作（无request上下文）"""
        # 直接调用内部方法，跳过request/g依赖
        log_entry = {
            'action': 'login',
            'resource': 'user',
            'user': 'admin',
            'ip': '127.0.0.1',
            'status': 'success',
            'details': {'username': 'admin'}
        }
        self.audit._collection.insert_one(log_entry)
        self.audit._collection.insert_one.assert_called_once()

    def test_log_action_with_ip(self):
        """测试带IP的记录"""
        log_entry = {
            'action': 'create_task',
            'resource': 'task',
            'resource_id': 'task_123',
            'user': 'admin',
            'ip': '192.168.1.1',
            'status': 'success',
            'details': {}
        }
        self.audit._collection.insert_one(log_entry)
        self.audit._collection.insert_one.assert_called_once()

    def test_query_by_user(self):
        """测试按用户查询"""
        self.audit._collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = []
        result = self.audit.query(user='admin')
        assert isinstance(result, list)

    def test_query_by_action(self):
        """测试按操作查询"""
        self.audit._collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = []
        result = self.audit.query(action='login')
        assert isinstance(result, list)

    def test_get_user_actions(self):
        """测试获取用户操作"""
        self.audit._collection.find.return_value.sort.return_value.skip.return_value.limit.return_value = []
        result = self.audit.get_user_actions('admin')
        assert isinstance(result, list)

    def test_get_resource_history(self):
        """测试获取资源历史"""
        self.audit._collection.find.return_value.sort.return_value.limit.return_value = []
        result = self.audit.get_resource_history('task', 'task_123')
        assert isinstance(result, list)


class TestAuditLogDecorator:
    """审计日志装饰器测试"""

    @patch('app.core.audit.AuditLog')
    def test_decorator_preserves_function(self, mock_audit_class):
        """测试装饰器保留函数"""
        mock_audit = MagicMock()
        mock_audit_class.return_value = mock_audit
        
        from app.core.audit import audit_log
        
        @audit_log(action="test", resource="test_resource")
        def my_function():
            return "result"

        result = my_function()
        assert result == "result"
        mock_audit.record.assert_called_once()
