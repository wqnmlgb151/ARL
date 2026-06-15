# -*- coding: utf-8 -*-
"""
ARL 分布式限流工具
基于 Redis 实现多 Worker 共享限流状态
"""

import time
import logging
from typing import Optional, Tuple
from functools import wraps

from flask import request, jsonify

from app.utils.redis_utils import redis_manager

logger = logging.getLogger(__name__)


class RedisRateLimiter:
    """
    基于 Redis 的分布式限流器
    使用滑动窗口算法实现精确限流
    """

    def __init__(self, redis_client=None):
        """
        初始化限流器

        Args:
            redis_client: Redis 客户端，如果为 None 则使用全局 redis_manager
        """
        self._redis = redis_client or redis_manager.client
        self._enabled = redis_manager.enabled and self._redis is not None

    def is_allowed(self, key: str, limit: int, window: int = 60) -> Tuple[bool, dict]:
        """
        检查请求是否允许

        Args:
            key: 限流键（如 IP 地址、用户ID）
            limit: 窗口内允许的最大请求数
            window: 时间窗口（秒）

        Returns:
            (是否允许, 限流信息)
        """
        if not self._enabled:
            # Redis 未启用，允许请求
            return True, {"limit": limit, "remaining": limit, "reset": 0}

        try:
            current_time = time.time()
            window_start = current_time - window

            # 使用 Redis MULTI/EXEC 保证原子性（单次往返完成所有操作）
            pipe = self._redis.pipeline()

            # 移除窗口外的旧记录
            pipe.zremrangebyscore(key, 0, window_start)

            # 添加当前请求记录
            member = f"{current_time}"
            pipe.zadd(key, {member: current_time})

            # 获取窗口内的请求数和最早的记录（在同一 pipeline 中）
            pipe.zcard(key)
            pipe.zrange(key, 0, 0, withscores=True)

            # 设置过期时间（防止内存泄漏）
            pipe.expire(key, window * 2)

            # 执行所有命令（单次网络往返）
            results = pipe.execute()
            current_count = results[2]  # zcard 的结果
            oldest = results[3]  # zrange 的结果

            # 计算剩余配额
            remaining = max(0, limit - current_count)

            # 获取最早记录的过期时间
            reset_time = int(oldest[0][1] + window - current_time) if oldest else window

            info = {
                "limit": limit,
                "remaining": remaining,
                "reset": reset_time,
                "window": window
            }

            if current_count > limit:
                return False, info

            return True, info

        except Exception as e:
            logger.error(f"Rate limiter error: {e}")
            # 出错时允许请求
            return True, {"limit": limit, "remaining": limit, "reset": 0}

    def get_usage(self, key: str, window: int = 60) -> dict:
        """
        获取限流使用情况

        Args:
            key: 限流键
            window: 时间窗口

        Returns:
            使用情况
        """
        if not self._enabled:
            return {"count": 0, "window": window}

        try:
            current_time = time.time()
            window_start = current_time - window

            count = self._redis.zcount(key, window_start, current_time)

            return {
                "count": count,
                "window": window,
                "start": window_start,
                "end": current_time
            }
        except Exception as e:
            logger.error(f"Error getting rate limit usage: {e}")
            return {"count": 0, "window": window}

    def reset(self, key: str) -> bool:
        """
        重置限流计数

        Args:
            key: 限流键

        Returns:
            是否成功
        """
        if not self._enabled:
            return False

        try:
            return self._redis.delete(key) > 0
        except Exception as e:
            logger.error(f"Error resetting rate limiter: {e}")
            return False


# 全局限流器实例
rate_limiter = RedisRateLimiter()


def get_rate_limiter() -> RedisRateLimiter:
    """获取全局限流器实例"""
    return rate_limiter


def rate_limit(limit: int = 60, window: int = 60, key_func=None):
    """
    限流装饰器

    Args:
        limit: 窗口内允许的最大请求数
        window: 时间窗口（秒）
        key_func: 自定义限流键生成函数，默认使用 IP 地址

    Usage:
        @rate_limit(limit=100, window=60)
        def my_view():
            return "OK"

        # 使用自定义键（如用户ID）
        @rate_limit(limit=10, window=60, key_func=lambda: g.user.get('id'))
        def user_view():
            return "OK"
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # 生成限流键
            if key_func:
                key = key_func()
            else:
                key = f"rate_limit:{request.remote_addr}"

            # 检查限流
            allowed, info = rate_limiter.is_allowed(key, limit, window)

            if not allowed:
                response = jsonify({
                    "code": 429,
                    "message": "Too many requests",
                    "success": False,
                    "retry_after": info["reset"]
                })
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = '0'
                response.headers['X-RateLimit-Reset'] = str(info['reset'])
                response.headers['Retry-After'] = str(info['reset'])
                return response, 429

            # 执行原函数
            result = f(*args, **kwargs)

            # 添加限流头
            if isinstance(result, tuple):
                response = result[0]
            else:
                response = result

            if hasattr(response, 'headers'):
                response.headers['X-RateLimit-Limit'] = str(info['limit'])
                response.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                response.headers['X-RateLimit-Reset'] = str(info['reset'])

            return result

        return decorated
    return decorator


# 预定义的限流配置
RATE_LIMIT_CONFIGS = {
    "default": {"limit": 60, "window": 60},      # 每分钟 60 次
    "strict": {"limit": 30, "window": 60},        # 每分钟 30 次
    "lenient": {"limit": 120, "window": 60},      # 每分钟 120 次
    "burst": {"limit": 10, "window": 1},          # 每秒 10 次
    "api": {"limit": 100, "window": 60},          # API 每分钟 100 次
    "login": {"limit": 5, "window": 300},         # 登录 5 分钟 5 次
}


def rate_limit_by_name(name: str):
    """
    使用预定义配置的限流装饰器

    Args:
        name: 配置名称

    Usage:
        @rate_limit_by_name("api")
        def my_api():
            return "OK"
    """
    config = RATE_LIMIT_CONFIGS.get(name, RATE_LIMIT_CONFIGS["default"])
    return rate_limit(limit=config["limit"], window=config["window"])
