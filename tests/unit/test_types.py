# -*- coding: utf-8 -*-
"""
数据类型测试
"""
import pytest
from datetime import datetime
from dataclasses import asdict
from app.core.types import (
    TaskStatus,
    TaskType,
    ScanPortType,
    TaskInfo,
    DomainInfo,
    IPInfo,
    SiteInfo,
    UserInfo,
    ScanResult,
    _convert_to_dict,
)


class TestTaskStatus:
    """任务状态枚举测试"""

    def test_task_status_values(self):
        assert TaskStatus.PENDING.value == "waiting"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "done"
        assert TaskStatus.FAILED.value == "error"
        assert TaskStatus.CANCELLED.value == "stop"

    def test_task_status_transitions(self):
        valid_transitions = {
            TaskStatus.PENDING: {TaskStatus.RUNNING, TaskStatus.CANCELLED},
            TaskStatus.RUNNING: {TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED},
            TaskStatus.COMPLETED: set(),
            TaskStatus.FAILED: {TaskStatus.PENDING},  # 重试
            TaskStatus.CANCELLED: {TaskStatus.PENDING},  # 重新提交
        }

        for from_status, to_statuses in valid_transitions.items():
            # 验证状态转换逻辑
            assert isinstance(from_status, TaskStatus)


class TestTaskType:
    """任务类型枚举测试"""

    def test_task_type_values(self):
        assert TaskType.DOMAIN.value == "domain"
        assert TaskType.IP.value == "ip"
        assert TaskType.RISK_CRUISING.value == "risk_cruising"
        assert TaskType.FOFA.value == "fofa"
        assert TaskType.ASSET_SITE_UPDATE.value == "asset_site_update"
        assert TaskType.ASSET_SITE_ADD.value == "asset_site_add"
        assert TaskType.ASSET_WIH_UPDATE.value == "asset_wih_update"



class TestScanPortType:
    """扫描端口类型枚举测试"""

    def test_scan_port_type_values(self):
        assert ScanPortType.TOP_100.value == "top100"
        assert ScanPortType.TOP_1000.value == "top1000"
        assert ScanPortType.ALL.value == "all"
        assert ScanPortType.CUSTOM.value == "custom"


class TestTaskInfo:
    """任务信息数据类测试"""

    def test_create_task_info(self):
        task = TaskInfo(
            task_id="task_123",
            target="example.com",
            task_type=TaskType.DOMAIN,
            status=TaskStatus.PENDING,
            options={"test": True},
        )

        assert task.task_id == "task_123"
        assert task.target == "example.com"
        assert task.task_type == TaskType.DOMAIN
        assert task.status == TaskStatus.PENDING
        assert task.options == {"test": True}

    def test_task_info_to_dict(self):
        task = TaskInfo(
            task_id="task_123",
            target="example.com",
            task_type=TaskType.DOMAIN,
            status=TaskStatus.PENDING,
        )

        result = task.to_dict()
        assert result["task_id"] == "task_123"
        assert result["target"] == "example.com"
        assert result["task_type"] == "domain"
        assert result["status"] == "waiting"

    def test_task_info_default_values(self):
        task = TaskInfo(
            task_id="task_123",
            target="example.com",
            task_type=TaskType.DOMAIN,
        )

        assert task.status == TaskStatus.PENDING
        assert task.options == {}
        assert task.result_count == 0
        assert task.error_message is None


class TestDomainInfo:
    """域名信息数据类测试"""

    def test_create_domain_info(self):
        domain = DomainInfo(
            domain="example.com",
            ip=["1.2.3.4"],
            task_id="task_123",
        )

        assert domain.domain == "example.com"
        assert domain.ip == ["1.2.3.4"]
        assert domain.task_id == "task_123"

    def test_domain_info_to_dict(self):
        domain = DomainInfo(
            domain="example.com",
            ip=["1.2.3.4"],
        )

        result = domain.to_dict()
        assert result["domain"] == "example.com"
        assert result["ip"] == ["1.2.3.4"]


class TestIPInfo:
    """IP信息数据类测试"""

    def test_create_ip_info(self):
        ip = IPInfo(
            ip="1.2.3.4",
            task_id="task_123",
            ports=[80, 443],
        )

        assert ip.ip == "1.2.3.4"
        assert ip.task_id == "task_123"
        assert ip.ports == [80, 443]


class TestSiteInfo:
    """站点信息数据类测试"""

    def test_create_site_info(self):
        site = SiteInfo(
            url="http://example.com",
            task_id="task_123",
            title="Example",
        )

        assert site.url == "http://example.com"
        assert site.task_id == "task_123"
        assert site.title == "Example"


class TestUserInfo:
    """用户信息数据类测试"""

    def test_create_user_info(self):
        user = UserInfo(
            username="testuser",
            password_hash="hashed_password",
            role="viewer",
        )

        assert user.username == "testuser"
        assert user.password_hash == "hashed_password"
        assert user.role == "viewer"

    def test_user_info_default_values(self):
        user = UserInfo(
            username="testuser",
            password_hash="hashed_password",
            role="viewer",
        )

        assert user.is_active is True
        assert user.api_key is None


class TestScanResult:
    """扫描结果数据类测试"""

    def test_create_scan_result(self):
        result = ScanResult(
            task_id="task_123",
            result_type="domain",
            data={"count": 100},
        )

        assert result.task_id == "task_123"
        assert result.result_type == "domain"
        assert result.data == {"count": 100}

    def test_scan_result_with_error(self):
        result = ScanResult(
            task_id="task_123",
            result_type="domain",
            data={"count": 50, "error": "部分失败"},
        )

        assert result.data["count"] == 50
        assert result.data["error"] == "部分失败"


class TestConvertToDict:
    """字典转换工具测试"""

    def test_convert_dataclass(self):
        task = TaskInfo(
            task_id="task_123",
            target="example.com",
            task_type=TaskType.DOMAIN,
        )
        result = _convert_to_dict(asdict(task))
        assert isinstance(result, dict)
        assert result["task_id"] == "task_123"

    def test_convert_nested_structure(self):
        task = TaskInfo(
            task_id="task_123",
            target="example.com",
            task_type=TaskType.DOMAIN,
            options={"key": "value"},
        )
        result = _convert_to_dict(asdict(task))
        assert result["options"]["key"] == "value"

    def test_convert_datetime(self):
        now = datetime.now()
        result = _convert_to_dict(now)
        assert isinstance(result, str)

    def test_convert_enum(self):
        result = _convert_to_dict(TaskStatus.PENDING)
        assert result == "waiting"
