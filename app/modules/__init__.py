from .ipInfo import PortInfo, IPInfo
from .baseInfo import BaseInfo
from .domainInfo import DomainInfo
from .pageInfo import PageInfo
from .wihRecord import WihRecord
from app.config import Config


class ScanPortType:
    TEST = Config.TOP_10
    TOP100 = Config.TOP_100
    TOP1000 = Config.TOP_1000
    ALL = "0-65535"


class DomainDictType:
    TEST = Config.DOMAIN_DICT_TEST
    BIG = Config.DOMAIN_DICT_2W


class CollectSource:
    DOMAIN_BRUTE = "domain_brute"
    BAIDU = "baidu"
    ALTDNS = "alt_dns"
    ARL = "arl"
    SITESPIDER = "site_spider"
    SEARCHENGINE = "search_engine"
    MONITOR = "monitor"


class TaskStatus:
    WAITING = "waiting"
    DONE = "done"
    ERROR = "error"
    STOP = "stop"


class TaskScheduleStatus:
    DONE = "done"
    SCHEDULED = "scheduled"
    STOP = "stop"
    ERROR = "error"


class TaskTag:
    """任务标签"""

    """带资产发现的任务"""
    TASK = "task"

    """域名监控任务"""
    MONITOR = "monitor"

    """风险巡航任务"""
    RISK_CRUISING = "risk_cruising"


class TaskType:
    """任务目标类别"""

    """IP任务"""
    IP = "ip"

    """域名任务"""
    DOMAIN = "domain"

    """站点， 风险巡航"""
    RISK_CRUISING = "risk_cruising"

    """资产站点更新"""
    ASSET_SITE_UPDATE = "asset_site_update"

    """Fofa 任务"""
    FOFA = "fofa"

    """资产站点添加"""
    ASSET_SITE_ADD = "asset_site_add"

    """资产 WIH 更新"""
    ASSET_WIH_UPDATE = "asset_wih_update"


class SiteAutoTag:
    ENTRY = "入口"
    INVALID = "无效"


class TaskSyncStatus:
    WAITING = "waiting"
    RUNNING = "running"
    ERROR = "error"
    DEFAULT = "default"


class SchedulerStatus:
    RUNNING = "running"
    STOP = "stop"


class AssetScopeType:
    DOMAIN = "domain"
    IP = "ip"


class PoCCategory:
    POC = "漏洞PoC"
    SNIFFER = "协议识别"
    SYSTEM_BRUTE = "服务弱口令"
    WEBB_RUTE = "应用弱口令"


class WebSiteFetchOption:
    # 针对WEB站点，可选功能选项
    SITE_CAPTURE = "site_capture"
    SEARCH_ENGINES = "search_engines"
    SITE_SPIDER = "site_spider"
    FILE_LEAK = "file_leak"
    POC_RUN = "poc_config"
    SITE_IDENTIFY = "site_identify"
    NUCLEI_SCAN = "nuclei_scan"  # nuclei 扫描
    Info_Hunter = "web_info_hunter"  # 对 JS 调用WebInfoHunter


class WebSiteFetchStatus:
    # 针对WEB站点任务可能的状态
    FETCH_SITE = "fetch_site"
    SITE_CAPTURE = "site_capture"
    SEARCH_ENGINES = "search_engines"
    SITE_SPIDER = "site_spider"
    FILE_LEAK = "file_leak"
    SITE_IDENTIFY = "site_identify"
    POC_RUN = "poc_run"
    NUCLEI_SCAN = "nuclei_scan"
    Info_Hunter = "web_info_hunter"  # 对 JS 调用WebInfoHunter


class CeleryRoutingKey:
    ASSET_TASK = "arltask"
    GITHUB_TASK = "arlgithub"


class CeleryAction:
    """celery任务celery_action字段"""

    """常规IP任务"""
    IP_TASK = "ip_task"

    """常规域名任务"""
    DOMAIN_TASK = "domain_task"

    """域名监测任务"""
    DOMAIN_EXEC_TASK = "domain_exec_task"

    """IP 类型监测任务"""
    IP_EXEC_TASK = "ip_exec_task"

    """同步已有任务"""
    DOMAIN_TASK_SYNC_TASK = "domain_task_sync_task"

    """PoC运行任务"""
    RUN_RISK_CRUISING = "run_risk_cruising"

    """Fofa 查询任务"""
    FOFA_TASK = "fofa_task"

    """Github 泄漏任务"""
    GITHUB_TASK_TASK = "github_task_task"

    """Github 泄漏监控任务"""
    GITHUB_TASK_MONITOR = "github_task_monitor"

    """资产站点更新任务"""
    ASSET_SITE_UPDATE = "asset_site_update"

    """资产站点添加站点"""
    ADD_ASSET_SITE_TASK = "add_asset_site_task"

    """资产WIH更新任务"""
    ASSET_WIH_UPDATE = "asset_wih_update"


# 错误码从 JSON 数据文件加载（app/dicts/error_codes.json）
import json as _json
import os as _os

_error_path = _os.path.join(_os.path.dirname(__file__), '..', 'dicts', 'error_codes.json')
_error_path = _os.path.abspath(_error_path)
try:
    with open(_error_path, 'r', encoding='utf-8') as _f:
        error_map = _json.load(_f)
except (FileNotFoundError, _json.JSONDecodeError) as _e:
    # 数据文件损坏或缺失时无法启动 — 立即失败并给出清晰错误信息
    import sys as _sys
    import logging as _logging
    _logging.getLogger(__name__).error(f"Failed to load error codes from {_error_path}: {_e}")
    _sys.exit(1)


class ErrorMsg:
    """错误消息（属性从 error_map 动态生成）"""
    pass


for _key, _value in error_map.items():
    setattr(ErrorMsg, _key, _value)

