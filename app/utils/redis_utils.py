# -*- coding: utf-8 -*-
"""
ARL Redis 缓存工具模块
提供统一的 Redis 连接管理和缓存操作
"""

import json
import logging
from typing import Optional, Any, Callable
from functools import wraps

try:
    import redis
    from redis import ConnectionPool
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from app.utils.string_utils import gen_md5

logger = logging.getLogger(__name__)


class RedisManager:
    """Redis 连接管理器"""

    def __init__(self):
        self._pool: Optional[ConnectionPool] = None
        self._client: Optional[redis.Redis] = None
        self._enabled: bool = False

    def init_app(self, config: dict) -> None:
        """
        初始化 Redis 连接

        Args:
            config: 配置字典，包含 REDIS_HOST, REDIS_PORT, REDIS_DB, REDIS_PASSWORD
        """
        if not REDIS_AVAILABLE:
            logger.warning("Redis package not installed, caching disabled")
            return

        try:
            host = config.get('REDIS_HOST', 'localhost')
            port = config.get('REDIS_PORT', 6379)
            db = config.get('REDIS_DB', 0)
            password = config.get('REDIS_PASSWORD', None)

            self._pool = ConnectionPool(
                host=host,
                port=port,
                db=db,
                password=password,
                decode_responses=True,
                max_connections=20
            )

            self._client = redis.Redis(connection_pool=self._pool)

            # 测试连接
            self._client.ping()
            self._enabled = True
            logger.info(f"Redis connected to {host}:{port}/{db}")

        except redis.ConnectionError as e:
            logger.error(f"Redis connection failed: {e}")
            self._enabled = False
        except Exception as e:
            logger.error(f"Redis initialization error: {e}")
            self._enabled = False

    @property
    def enabled(self) -> bool:
        """是否启用缓存"""
        return self._enabled and self._client is not None

    @property
    def client(self) -> Optional[redis.Redis]:
        """获取 Redis 客户端"""
        return self._client if self.enabled else None

    def get(self, key: str) -> Optional[Any]:
        """
        获取缓存值

        Args:
            key: 缓存键

        Returns:
            缓存值，不存在返回 None
        """
        if not self.enabled:
            return None

        try:
            value = self._client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Redis get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        设置缓存值

        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间（秒），默认1小时

        Returns:
            是否成功
        """
        if not self.enabled:
            return False

        try:
            serialized = json.dumps(value, default=str)
            self._client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Redis set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """
        删除缓存值

        Args:
            key: 缓存键

        Returns:
            是否成功
        """
        if not self.enabled:
            return False

        try:
            return self._client.delete(key) > 0
        except Exception as e:
            logger.error(f"Redis delete error for key {key}: {e}")
            return False

    def exists(self, key: str) -> bool:
        """
        检查键是否存在

        Args:
            key: 缓存键

        Returns:
            是否存在
        """
        if not self.enabled:
            return False

        try:
            return self._client.exists(key) > 0
        except Exception as e:
            logger.error(f"Redis exists error for key {key}: {e}")
            return False

    def clear_pattern(self, pattern: str) -> int:
        """
        清除匹配模式的所有键（使用 SCAN 避免阻塞 Redis）

        Args:
            pattern: 匹配模式，如 "dns:*"

        Returns:
            清除的键数量
        """
        if not self.enabled:
            return 0

        try:
            deleted = 0
            # 使用 scan_iter 分批获取键，避免 KEYS 命令阻塞 Redis
            for key in self._client.scan_iter(match=pattern, count=100):
                self._client.delete(key)
                deleted += 1
            return deleted
        except Exception as e:
            logger.error(f"Redis clear_pattern error for pattern {pattern}: {e}")
            return 0

    def get_stats(self) -> dict:
        """
        获取 Redis 统计信息

        Returns:
            统计信息字典
        """
        if not self.enabled:
            return {"enabled": False}

        try:
            info = self._client.info()
            return {
                "enabled": True,
                "used_memory": info.get("used_memory_human", "N/A"),
                "connected_clients": info.get("connected_clients", 0),
                "total_keys": self._client.dbsize(),
                "uptime_seconds": info.get("uptime_in_seconds", 0)
            }
        except Exception as e:
            logger.error(f"Redis get_stats error: {e}")
            return {"enabled": True, "error": str(e)}

    def close(self) -> None:
        """关闭 Redis 连接"""
        if self._pool:
            self._pool.disconnect()
            logger.info("Redis connection closed")


# 全局 Redis 管理器实例
redis_manager = RedisManager()


def cache_result(ttl: int = 3600, key_prefix: str = "", key_builder: Optional[Callable] = None):
    """
    缓存装饰器

    Args:
        ttl: 缓存过期时间（秒），默认1小时
        key_prefix: 缓存键前缀
        key_builder: 自定义缓存键生成函数

    Usage:
        @cache_result(ttl=3600, key_prefix="dns")
        def query_dns(domain):
            # ... 查询逻辑
            return result
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 生成缓存键
            if key_builder:
                cache_key = key_builder(*args, **kwargs)
            else:
                # 默认键生成：使用 JSON 序列化确保稳定性
                # 跳过 self/cls 如果存在（检测是否为方法调用）
                call_args = args
                if args and isinstance(args[0], (type, object)):
                    # 可能是实例方法或类方法
                    call_args = args[1:]

                try:
                    args_key = json.dumps(call_args, sort_keys=True, default=str)
                    kwargs_key = json.dumps(kwargs, sort_keys=True, default=str)
                    key_hash = gen_md5(f"{args_key}:{kwargs_key}")
                except (TypeError, ValueError):
                    # 回退到字符串表示
                    args_str = str(call_args) if call_args else ""
                    kwargs_str = str(sorted(kwargs.items()))
                    key_hash = gen_md5(f"{args_str}:{kwargs_str}")

                cache_key = f"{key_prefix}:{func.__name__}:{key_hash}" if key_prefix else f"{func.__name__}:{key_hash}"

            # 尝试从缓存获取
            cached = redis_manager.get(cache_key)
            if cached is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached

            # 执行函数
            result = func(*args, **kwargs)

            # 存入缓存
            if result is not None:
                redis_manager.set(cache_key, result, ttl)
                logger.debug(f"Cache set: {cache_key}, ttl={ttl}")

            return result
        return wrapper
    return decorator


def invalidate_cache(key_prefix: str, *args, **kwargs):
    """
    使缓存失效

    Args:
        key_prefix: 缓存键前缀
        *args, **kwargs: 传递给缓存键生成函数的参数
    """
    if args or kwargs:
        # 生成特定键
        args_str = str(args)
        kwargs_str = str(sorted(kwargs.items()))
        key_hash = gen_md5(f"{args_str}:{kwargs_str}")
        cache_key = f"{key_prefix}:{key_hash}"
        redis_manager.delete(cache_key)
    else:
        # 清除所有匹配前缀的键
        redis_manager.clear_pattern(f"{key_prefix}:*")
