# -*- coding: utf-8 -*-
"""
ARL 服务接口定义
定义所有服务的标准接口
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ServiceConfig:
    """服务配置"""
    name: str
    host: str = "localhost"
    port: int = 0
    timeout: int = 30
    max_retries: int = 3


@dataclass
class ServiceStatus:
    """服务状态"""
    name: str
    status: str  # "running", "stopped", "error"
    uptime: int = 0
    error: Optional[str] = None


class ServiceInterface(ABC):
    """服务接口基类"""

    @abstractmethod
    def start(self) -> bool:
        """启动服务"""
        pass

    @abstractmethod
    def stop(self) -> bool:
        """停止服务"""
        pass

    @abstractmethod
    def restart(self) -> bool:
        """重启服务"""
        pass

    @abstractmethod
    def get_status(self) -> ServiceStatus:
        """获取服务状态"""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """健康检查"""
        pass


class DnsServiceInterface(ServiceInterface):
    """DNS 解析服务接口"""

    @abstractmethod
    def query_a(self, domain: str) -> List[str]:
        """查询 A 记录"""
        pass

    @abstractmethod
    def query_cname(self, domain: str) -> List[str]:
        """查询 CNAME 记录"""
        pass

    @abstractmethod
    def query_mx(self, domain: str) -> List[str]:
        """查询 MX 记录"""
        pass

    @abstractmethod
    def query_ns(self, domain: str) -> List[str]:
        """查询 NS 记录"""
        pass

    @abstractmethod
    def query_txt(self, domain: str) -> List[str]:
        """查询 TXT 记录"""
        pass

    @abstractmethod
    def batch_query(self, domains: List[str], record_type: str) -> Dict[str, List[str]]:
        """批量查询"""
        pass

    @abstractmethod
    def clear_cache(self, domain: Optional[str] = None) -> None:
        """清除缓存"""
        pass


class ScanServiceInterface(ServiceInterface):
    """端口扫描服务接口"""

    @abstractmethod
    def scan_ports(self, target: str, ports: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """扫描端口"""
        pass

    @abstractmethod
    def scan_os(self, target: str) -> Dict[str, Any]:
        """扫描操作系统"""
        pass

    @abstractmethod
    def scan_services(self, target: str, ports: List[int]) -> List[Dict[str, Any]]:
        """扫描服务"""
        pass

    @abstractmethod
    def batch_scan(self, targets: List[str], options: Dict[str, Any]) -> List[Dict[str, Any]]:
        """批量扫描"""
        pass


class TaskServiceInterface(ServiceInterface):
    """任务调度服务接口"""

    @abstractmethod
    def create_task(self, task_type: str, target: str, options: Dict[str, Any]) -> str:
        """创建任务"""
        pass

    @abstractmethod
    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        pass

    @abstractmethod
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        pass

    @abstractmethod
    def retry_task(self, task_id: str) -> bool:
        """重试任务"""
        pass

    @abstractmethod
    def list_tasks(self, status: Optional[str] = None, limit: int = 100) -> List[Dict[str, Any]]:
        """列出任务"""
        pass


class DataServiceInterface(ServiceInterface):
    """数据处理服务接口"""

    @abstractmethod
    def clean_data(self, data: List[Dict[str, Any]], data_type: str) -> List[Dict[str, Any]]:
        """清洗数据"""
        pass

    @abstractmethod
    def aggregate_data(self, data: List[Dict[str, Any]], group_by: str) -> Dict[str, Any]:
        """聚合数据"""
        pass

    @abstractmethod
    def export_data(self, data: List[Dict[str, Any]], format: str, output_path: str) -> str:
        """导出数据"""
        pass

    @abstractmethod
    def import_data(self, file_path: str, data_type: str) -> List[Dict[str, Any]]:
        """导入数据"""
        pass


class MonitorServiceInterface(ServiceInterface):
    """监控告警服务接口"""

    @abstractmethod
    def collect_metrics(self) -> Dict[str, Any]:
        """收集指标"""
        pass

    @abstractmethod
    def check_alert_rules(self) -> List[Dict[str, Any]]:
        """检查告警规则"""
        pass

    @abstractmethod
    def send_alert(self, alert: Dict[str, Any], channels: List[str]) -> bool:
        """发送告警"""
        pass

    @abstractmethod
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        pass


class CacheServiceInterface(ServiceInterface):
    """缓存服务接口"""

    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """设置缓存"""
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """删除缓存"""
        pass

    @abstractmethod
    def exists(self, key: str) -> bool:
        """检查键是否存在"""
        pass

    @abstractmethod
    def clear_pattern(self, pattern: str) -> int:
        """清除匹配模式的缓存"""
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        pass
