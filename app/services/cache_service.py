# -*- coding: utf-8 -*-
"""
ARL 多级缓存服务
L1（进程内 LRU）+ L2（Redis）缓存架构

注意：简单缓存请使用 redis_utils.cache_result 装饰器
此模块提供需要 L1+L2 多级缓存的高级场景
"""
import time
import logging
import threading
import random
from typing import Any, Optional
from collections import OrderedDict
from dataclasses import dataclass
from app.utils.redis_utils import redis_manager

logger = logging.getLogger(__name__)

@dataclass
class CacheConfig:
    l1_max_size: int = 1000
    l1_ttl: float = 60.0
    l2_ttl: float = 300.0
    enable_l1: bool = True
    enable_l2: bool = True
    ttl_jitter: float = 0.1

class LRUCache:
    def __init__(self, max_size=1000, default_ttl=60.0):
        self._cache = OrderedDict()
        self._expire_times = {}
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
    
    def get(self, key):
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None
            expire_time = self._expire_times.get(key, 0)
            if expire_time > 0 and time.time() > expire_time:
                del self._cache[key]
                del self._expire_times[key]
                self._misses += 1
                return None
            self._cache.move_to_end(key)
            self._hits += 1
            return self._cache[key]
    
    def set(self, key, value, ttl=None):
        ttl = ttl or self._default_ttl
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._expire_times[key]
            while len(self._cache) >= self._max_size:
                oldest_key, _ = self._cache.popitem(last=False)
                del self._expire_times[oldest_key]
            self._cache[key] = value
            self._expire_times[key] = time.time() + ttl
    
    def delete(self, key):
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                del self._expire_times[key]
                return True
            return False
    
    def clear(self):
        with self._lock:
            self._cache.clear()
            self._expire_times.clear()
    
    def get_stats(self):
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0
        return {'size': len(self._cache), 'max_size': self._max_size, 'hits': self._hits, 'misses': self._misses, 'hit_rate': hit_rate}

class MultiLevelCache:
    def __init__(self, config=None):
        self.config = config or CacheConfig()
        self.l1 = LRUCache(self.config.l1_max_size, self.config.l1_ttl) if self.config.enable_l1 else None
        self.l2_enabled = self.config.enable_l2 and redis_manager.enabled
    
    def _l2_key(self, key):
        return f'mlc:{key}'
    
    def _l2_ttl(self, ttl=None):
        base_ttl = ttl or self.config.l2_ttl
        jitter = base_ttl * self.config.ttl_jitter * (2 * random.random() - 1)
        return base_ttl + jitter
    
    def get(self, key):
        if self.l1:
            value = self.l1.get(key)
            if value is not None:
                return value
        if self.l2_enabled:
            l2_key = self._l2_key(key)
            value = redis_manager.get(l2_key)
            if value is not None:
                if self.l1:
                    self.l1.set(key, value, self.config.l1_ttl)
                return value
        return None
    
    def set(self, key, value, ttl=None, l1_ttl=None, l2_ttl=None):
        if self.l1:
            self.l1.set(key, value, l1_ttl or self.config.l1_ttl)
        if self.l2_enabled:
            l2_key = self._l2_key(key)
            actual_l2_ttl = l2_ttl or self._l2_ttl(ttl)
            redis_manager.set(l2_key, value, int(actual_l2_ttl))
    
    def delete(self, key):
        result = False
        if self.l1:
            result = self.l1.delete(key) or result
        if self.l2_enabled:
            l2_key = self._l2_key(key)
            result = redis_manager.delete(l2_key) or result
        return result
    
    def clear_pattern(self, pattern):
        if not self.l2_enabled:
            return 0
        return redis_manager.clear_pattern(f'mlc:{pattern}')
    
    def invalidate(self, key):
        self.delete(key)
    
    def get_stats(self):
        stats = {'l1_enabled': self.l1 is not None, 'l2_enabled': self.l2_enabled}
        if self.l1:
            stats['l1'] = self.l1.get_stats()
        return stats

# 全局多级缓存实例
multi_level_cache = MultiLevelCache()


def get_cache() -> MultiLevelCache:
    """获取全局多级缓存实例"""
    return multi_level_cache


# 预定义缓存策略（供参考）
CACHE_STRATEGIES = {
    'task_result': {'ttl': 300, 'l1_ttl': 60},
    'domain_info': {'ttl': 3600, 'l1_ttl': 300},
    'ip_info': {'ttl': 1800, 'l1_ttl': 300},
    'statistics': {'ttl': 60, 'l1_ttl': 30},
}
