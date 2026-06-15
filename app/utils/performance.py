# -*- coding: utf-8 -*-
"""
ARL 性能监控模块
提供性能统计和监控功能
"""

import time
import logging
import functools
import threading
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass, field
from collections import defaultdict, deque

logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """请求指标"""
    path: str
    method: str
    status_code: int
    duration: float
    timestamp: float


@dataclass
class EndpointStats:
    """端点统计"""
    total_requests: int = 0
    total_duration: float = 0.0
    min_duration: float = float('inf')
    max_duration: float = 0.0
    status_codes: Dict[int, int] = field(default_factory=lambda: defaultdict(int))
    recent_requests: deque = field(default_factory=lambda: deque(maxlen=100))

    @property
    def avg_duration(self) -> float:
        """平均耗时"""
        if self.total_requests == 0:
            return 0.0
        return self.total_duration / self.total_requests

    def record(self, duration: float, status_code: int) -> None:
        """记录请求"""
        self.total_requests += 1
        self.total_duration += duration
        self.min_duration = min(self.min_duration, duration)
        self.max_duration = max(self.max_duration, duration)
        self.status_codes[status_code] += 1

        # 使用 deque(maxlen=100) 自动限制大小，避免内存泄漏
        self.recent_requests.append({
            "duration": duration,
            "status_code": status_code,
            "timestamp": time.time()
        })


class PerformanceMonitor:
    """
    性能监控器
    收集和统计请求性能指标
    """

    def __init__(self):
        self._stats: Dict[str, EndpointStats] = defaultdict(EndpointStats)
        self._lock = threading.Lock()
        self._enabled = True

    def record_request(self, path: str, method: str, status_code: int, duration: float):
        """
        记录请求指标

        Args:
            path: 请求路径
            method: HTTP方法
            status_code: 状态码
            duration: 耗时（秒）
        """
        if not self._enabled:
            return

        key = f"{method}:{path}"
        with self._lock:
            self._stats[key].record(duration, status_code)

            # 慢请求警告
            if duration > 2.0:
                logger.warning(
                    f"Slow request: {method} {path} took {duration:.3f}s "
                    f"(status={status_code})"
                )

    def get_stats(self) -> Dict[str, Any]:
        """
        获取所有统计信息

        Returns:
            统计信息字典
        """
        with self._lock:
            stats = {}
            for key, endpoint_stats in self._stats.items():
                stats[key] = {
                    "total_requests": endpoint_stats.total_requests,
                    "avg_duration": endpoint_stats.avg_duration,
                    "min_duration": endpoint_stats.min_duration if endpoint_stats.min_duration != float('inf') else 0,
                    "max_duration": endpoint_stats.max_duration,
                    "status_codes": dict(endpoint_stats.status_codes)
                }
            return stats

    def get_slow_endpoints(self, threshold: float = 1.0, limit: int = 10) -> list:
        """
        获取慢请求端点

        Args:
            threshold: 耗时阈值（秒）
            limit: 返回数量限制

        Returns:
            慢请求端点列表
        """
        with self._lock:
            slow_endpoints = []
            for key, stats in self._stats.items():
                if stats.avg_duration > threshold:
                    slow_endpoints.append({
                        "endpoint": key,
                        "avg_duration": stats.avg_duration,
                        "total_requests": stats.total_requests
                    })

            # 按平均耗时排序
            slow_endpoints.sort(key=lambda x: x["avg_duration"], reverse=True)
            return slow_endpoints[:limit]

    def reset_stats(self):
        """重置所有统计"""
        with self._lock:
            self._stats.clear()

    def enable(self):
        """启用监控"""
        self._enabled = True

    def disable(self):
        """禁用监控"""
        self._enabled = False


# 全局性能监控器实例
performance_monitor = PerformanceMonitor()


def get_performance_monitor() -> PerformanceMonitor:
    """获取全局性能监控器实例"""
    return performance_monitor


def monitor_performance(func: Callable = None, *, threshold: float = 1.0):
    """
    性能监控装饰器

    Args:
        func: 被装饰的函数
        threshold: 慢请求阈值（秒）

    Usage:
        @monitor_performance
        def my_view():
            return "OK"

        @monitor_performance(threshold=0.5)
        def fast_view():
            return "OK"
    """
    def decorator(f):
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            result = f(*args, **kwargs)
            duration = time.time() - start_time

            # 记录性能
            from flask import request
            status_code = 200
            if isinstance(result, tuple) and len(result) > 1:
                status_code = result[1]

            performance_monitor.record_request(
                path=request.path,
                method=request.method,
                status_code=status_code,
                duration=duration
            )

            # 慢请求警告
            if duration > threshold:
                logger.warning(
                    f"Slow function: {f.__name__} took {duration:.3f}s "
                    f"(threshold={threshold}s)"
                )

            return result
        return wrapper

    if func is not None:
        return decorator(func)
    return decorator


def measure_time(func: Callable) -> Callable:
    """
    测量函数执行时间的装饰器

    Args:
        func: 被装饰的函数

    Returns:
        装饰后的函数

    Usage:
        @measure_time
        def slow_function():
            time.sleep(1)
            return "done"
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time

        logger.debug(
            f"Function {func.__name__} executed in {duration:.3f}s"
        )

        return result
    return wrapper


def get_performance_report() -> Dict[str, Any]:
    """
    生成性能报告

    Returns:
        性能报告字典
    """
    stats = performance_monitor.get_stats()
    slow_endpoints = performance_monitor.get_slow_endpoints(threshold=1.0)

    # 计算总请求数和平均响应时间
    total_requests = sum(s["total_requests"] for s in stats.values())
    total_duration = sum(s["avg_duration"] * s["total_requests"] for s in stats.values())
    avg_response_time = total_duration / total_requests if total_requests > 0 else 0

    return {
        "timestamp": time.time(),
        "total_requests": total_requests,
        "avg_response_time": avg_response_time,
        "endpoints": len(stats),
        "slow_endpoints": slow_endpoints,
        "endpoint_stats": stats
    }


# 性能统计API响应格式
def format_performance_response() -> Dict[str, Any]:
    """
    格式化性能统计为API响应

    Returns:
        API响应字典
    """
    report = get_performance_report()

    return {
        "code": 0,
        "message": "success",
        "success": True,
        "data": {
            "total_requests": report["total_requests"],
            "avg_response_time": f"{report['avg_response_time']:.3f}s",
            "endpoints_tracked": report["endpoints"],
            "slow_endpoints": report["slow_endpoints"][:5]  # 只返回前5个
        }
    }
