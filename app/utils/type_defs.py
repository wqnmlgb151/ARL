# -*- coding: utf-8 -*-
"""
DEPRECATED: ARL类型定义模块

此模块已被 app/modules/__init__.py（运行时常量）和 app/core/types.py（Enum 类型）取代。
新代码请使用上述两个模块，本文件保留用于向后兼容。

The authoritative type definitions are now in:
- app/modules/__init__.py  — TaskStatus, TaskType, CeleryAction (matches DB values)
- app/core/types.py        — Enum versions of the same
"""

from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from datetime import datetime


# 基础类型定义
IPAddress = str
DomainName = str
PortNumber = int
URL = str


@dataclass
class PortInfo:
    """端口信息数据类"""
    port: PortNumber
    service: str = ""
    version: str = ""
    state: str = "open"
    banner: str = ""


@dataclass
class IPInfo:
    """IP信息数据类"""
    ip: IPAddress
    ports: List[PortInfo] = field(default_factory=list)
    os: str = ""
    asn: str = ""
    country: str = ""
    city: str = ""
    isp: str = ""
    cdn: bool = False


@dataclass
class DomainInfo:
    """域名信息数据类"""
    domain: DomainName
    subdomain: str = ""
    fld: str = ""
    ips: List[IPAddress] = field(default_factory=list)
    cnames: List[str] = field(default_factory=list)
    mx: List[str] = field(default_factory=list)
    txt: List[str] = field(default_factory=list)


@dataclass
class SiteInfo:
    """站点信息数据类"""
    url: URL
    title: str = ""
    status_code: int = 0
    server: str = ""
    technologies: List[str] = field(default_factory=list)
    fingerprints: List[str] = field(default_factory=list)
    screenshot: str = ""


@dataclass
class TaskInfo:
    """任务信息数据类"""
    task_id: str
    name: str
    target: str
    status: str = "waiting"
    progress: float = 0.0
    create_time: datetime = field(default_factory=datetime.now)
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result_count: int = 0


@dataclass
class ScanOptions:
    """扫描选项数据类"""
    domain_brute: bool = True
    domain_brute_type: str = "big"
    port_scan: bool = True
    port_scan_type: str = "test"
    service_identify: bool = False
    os_identify: bool = False
    ssl_cert: bool = True
    skip_cdn: bool = True
    site_identify: bool = True
    search_engine: bool = True
    site_spider: bool = True
    site_screenshot: bool = False
    file_leak: bool = False
    host_collision: bool = False
    nuclei_poc: bool = False
    wih_call: bool = False
    dns_query_plugin: bool = True
    arl_search: bool = True


# 任务状态枚举
class TaskStatus:
    """任务状态常量"""
    WAITING: str = "waiting"
    RUNNING: str = "running"
    DONE: str = "done"
    ERROR: str = "error"
    STOP: str = "stop"


# 调度器状态枚举
class SchedulerStatus:
    """调度器状态常量"""
    RUNNING: str = "running"
    STOP: str = "stop"


# 任务类型枚举
class TaskType:
    """任务类型常量"""
    IP: str = "ip"
    DOMAIN: str = "domain"
    RISK_CRUISING: str = "risk_cruising"
    ASSET_SITE_UPDATE: str = "asset_site_update"
    FOFA: str = "fofa"
    ASSET_SITE_ADD: str = "asset_site_add"
    ASSET_WIH_UPDATE: str = "asset_wih_update"


# 资产范围类型枚举
class AssetScopeType:
    """资产范围类型常量"""
    DOMAIN: str = "domain"
    IP: str = "ip"


# 收集来源枚举
class CollectSource:
    """数据收集来源常量"""
    DOMAIN_BRUTE: str = "domain_brute"
    BAIDU: str = "baidu"
    ALTDNS: str = "alt_dns"
    ARL: str = "arl"
    SITESPIDER: str = "site_spider"
    SEARCHENGINE: str = "search_engine"
    MONITOR: str = "monitor"


# Celery动作类型枚举
class CeleryAction:
    """Celery任务动作类型"""
    DOMAIN_TASK_SYNC_TASK: str = "domain_task_sync_task"
    DOMAIN_EXEC_TASK: str = "domain_exec_task"
    IP_EXEC_TASK: str = "ip_exec_task"
    DOMAIN_TASK: str = "domain_task"
    IP_TASK: str = "ip_task"
    RUN_RISK_CRUISING: str = "run_risk_cruising"
    FOFA_TASK: str = "fofa_task"
    GITHUB_TASK_TASK: str = "github_task_task"
    GITHUB_TASK_MONITOR: str = "github_task_monitor"
    ASSET_SITE_UPDATE: str = "asset_site_update"
    ADD_ASSET_SITE_TASK: str = "add_asset_site_task"
    ASSET_WIH_UPDATE: str = "asset_wih_update"


# 数据库集合名称
class CollectionName:
    """MongoDB集合名称常量"""
    TASK: str = "task"
    DOMAIN: str = "domain"
    IP: str = "ip"
    SITE: str = "site"
    URL: str = "url"
    CERT: str = "cert"
    SERVICE: str = "service"
    FILELEAK: str = "fileleak"
    SCHEDULER: str = "scheduler"
    USER: str = "user"
    GITHUB_TASK: str = "github_task"
    GITHUB_RESULT: str = "github_result"
    GITHUB_SCHEDULER: str = "github_scheduler"
    POLICY: str = "policy"
    POC: str = "poc"
    VULN: str = "vuln"
    NUCLEI_RESULT: str = "nuclei_result"
    ASSET_SCOPE: str = "asset_scope"
    ASSET_DOMAIN: str = "asset_domain"
    ASSET_IP: str = "asset_ip"
    ASSET_SITE: str = "asset_site"
    CONSOLE: str = "console"
    CIP: str = "cip"
    FINGERPRINT: str = "fingerprint"
    STAT_FINGER: str = "stat_finger"
    TASK_SCHEDULE: str = "task_schedule"
    WIH: str = "wih"
    ASSET_WIH: str = "asset_wih"


# API响应类型
APIResponse = Dict[str, Any]
ErrorResponse = Dict[str, Any]
SuccessResponse = Dict[str, Any]


# 配置类型
ConfigDict = Dict[str, Any]
MongoConfig = Dict[str, str]
CeleryConfig = Dict[str, str]
ARLConfig = Dict[str, Any]


# 扫描结果类型
ScanResult = Dict[str, Any]
DomainResult = Dict[str, Any]
IPResult = Dict[str, Any]
SiteResult = Dict[str, Any]


# 导出格式类型
ExportFormat = str  # "json", "csv", "xlsx", "pdf"
