# -*- coding: utf-8 -*-
"""
ARL类型定义
使用dataclass定义数据类型，提供类型安全和序列化支持
"""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Dict, List, Optional
from enum import Enum


def _convert_to_dict(obj: Any) -> Any:
    """
    递归转换对象为字典，处理特殊类型

    Args:
        obj: 要转换的对象

    Returns:
        转换后的字典
    """
    if isinstance(obj, datetime):
        return obj.isoformat()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, dict):
        return {k: _convert_to_dict(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_convert_to_dict(item) for item in obj]
    return obj


class TaskStatus(Enum):
    """任务状态枚举（值与数据库中存储的字符串一致）"""
    WAITING = "waiting"
    RUNNING = "running"
    DONE = "done"
    ERROR = "error"
    STOP = "stop"

    # Legacy aliases for code migrated from earlier refactor phase
    PENDING = "waiting"
    COMPLETED = "done"
    FAILED = "error"
    CANCELLED = "stop"


class TaskType(Enum):
    """任务类型枚举（值与数据库中存储的字符串一致）"""
    IP = "ip"
    DOMAIN = "domain"
    RISK_CRUISING = "risk_cruising"
    ASSET_SITE_UPDATE = "asset_site_update"
    FOFA = "fofa"
    ASSET_SITE_ADD = "asset_site_add"
    ASSET_WIH_UPDATE = "asset_wih_update"



class ScanPortType(Enum):
    """扫描端口类型枚举"""
    TEST = "test"
    TOP_100 = "top100"
    TOP_1000 = "top1000"
    ALL = "all"
    CUSTOM = "custom"


@dataclass
class TaskInfo:
    """
    任务信息

    Attributes:
        task_id: 任务唯一标识
        target: 扫描目标（域名/IP/URL）
        task_type: 任务类型
        status: 任务状态
        options: 扫描选项
        created_at: 创建时间
        updated_at: 更新时间
        completed_at: 完成时间
        result_count: 结果数量
        error_message: 错误消息
    """
    task_id: str
    target: str
    task_type: TaskType
    status: TaskStatus = TaskStatus.WAITING
    options: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result_count: int = 0
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return _convert_to_dict(asdict(self))


@dataclass
class DomainInfo:
    """
    域名信息

    Attributes:
        domain: 域名
        ip: 解析IP列表
        task_id: 关联任务ID
        created_at: 创建时间
        whois: WHOIS信息
        dns记录: DNS解析记录
    """
    domain: str
    ip: List[str] = field(default_factory=list)
    task_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    whois: Optional[Dict[str, Any]] = None
    dns_records: Optional[Dict[str, List[str]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return _convert_to_dict(asdict(self))


@dataclass
class IPInfo:
    """
    IP信息

    Attributes:
        ip: IP地址
        task_id: 关联任务ID
        created_at: 创建时间
        geoip: 地理位置信息
        asn: ASN信息
        ports: 开放端口列表
        os: 操作系统指纹
    """
    ip: str
    task_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    geoip: Optional[Dict[str, Any]] = None
    asn: Optional[Dict[str, Any]] = None
    ports: List[int] = field(default_factory=list)
    os: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return _convert_to_dict(asdict(self))


@dataclass
class SiteInfo:
    """
    站点信息

    Attributes:
        url: 站点URL
        task_id: 关联任务ID
        status: 状态
        title: 页面标题
        http_status: HTTP状态码
        headers: HTTP响应头
        body_hash: 响应体哈希
        technologies: 使用的技术栈
        screenshot: 截图路径
        created_at: 创建时间
    """
    url: str
    task_id: Optional[str] = None
    status: str = "unknown"
    title: Optional[str] = None
    http_status: Optional[int] = None
    headers: Dict[str, str] = field(default_factory=dict)
    body_hash: Optional[str] = None
    technologies: List[str] = field(default_factory=list)
    screenshot: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return _convert_to_dict(asdict(self))


@dataclass
class UserInfo:
    """
    用户信息

    Attributes:
        username: 用户名
        password_hash: 密码哈希
        role: 用户角色
        api_key: API密钥
        is_active: 是否激活
        last_login: 最后登录时间
        created_at: 创建时间
        updated_at: 更新时间
    """
    username: str
    password_hash: str
    role: str = "viewer"
    api_key: Optional[str] = None
    is_active: bool = True
    last_login: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（不包含敏感信息）"""
        return {
            'username': self.username,
            'role': self.role,
            'is_active': self.is_active,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


@dataclass
class ScanResult:
    """
    扫描结果

    Attributes:
        task_id: 任务ID
        result_type: 结果类型（domain/ip/site）
        data: 结果数据
        created_at: 创建时间
    """
    task_id: str
    result_type: str
    data: Dict[str, Any]
    created_at: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return _convert_to_dict(asdict(self))


# 导出所有类型
__all__ = [
    'TaskStatus',
    'TaskType',
    'ScanPortType',
    'TaskInfo',
    'DomainInfo',
    'IPInfo',
    'SiteInfo',
    'UserInfo',
    'ScanResult'
]
