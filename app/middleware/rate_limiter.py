# -*- coding: utf-8 -*-
"""
速率限制中间件
使用 Flask-Limiter 实现 API 速率限制
"""

from flask import request, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address


# 全局 limiter 实例
limiter = None


def init_limiter(app):
    """
    初始化 Flask-Limiter
    
    使用内存存储，生产环境应使用 Redis:
    storage_uri="redis://localhost:6379"
    """
    global limiter
    
    limiter = Limiter(
        app=app,
        key_func=get_rate_limit_key,
        default_limits=["200 per hour", "50 per minute"],
        storage_uri="memory://",
        strategy="fixed-window"
    )
    
    return limiter


def get_rate_limit_key():
    """
    获取速率限制键
    
    优先使用 API Key，其次使用 IP 地址
    """
    # 尝试从 API Key 获取
    api_key = request.headers.get('X-API-Key') or request.headers.get('Token')
    if api_key:
        return f"apikey:{api_key[:16]}"  # 只取前16位作为键
    
    # 使用 IP 地址
    return f"ip:{get_remote_address()}"


def rate_limit_by_name(limit_string):
    """
    按名称设置速率限制的装饰器
    
    用法:
        @rate_limit_by_name("10 per minute")
        def my_endpoint():
            ...
    """
    def decorator(f):
        @limiter.limit(limit_string)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper
    return decorator


# 预定义的速率限制
LIMITS = {
    'login': '5 per minute',
    'register': '3 per hour',
    'password_reset': '3 per hour',
    'api_key': '10 per hour',
    'export': '10 per hour',
    'task_create': '30 per minute',
    'default': '100 per hour'
}


def get_limit(endpoint_type):
    """获取预定义的速率限制"""
    return LIMITS.get(endpoint_type, LIMITS['default'])
