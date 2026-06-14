# -*- coding: utf-8 -*-
"""
安全中间件
添加安全头和其他安全相关的中间件
"""

import os
import secrets
from functools import wraps
from flask import request, abort, current_app, g


def init_security_headers(app):
    """初始化安全头中间件"""

    @app.after_request
    def set_security_headers(response):
        # 内容安全策略（CSP）- 防止 XSS
        # 注意：'unsafe-inline' 允许内联脚本/样式（兼容性考虑）
        # 生产环境建议使用 nonce 或 hash 替代 'unsafe-inline'
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self' https:; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers['Content-Security-Policy'] = csp

        # 防止 MIME 类型嗅探
        response.headers['X-Content-Type-Options'] = 'nosniff'

        # 防止点击劫持
        response.headers['X-Frame-Options'] = 'DENY'

        # XSS 保护（旧版浏览器）
        response.headers['X-XSS-Protection'] = '1; mode=block'

        # 引用策略
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'

        # 权限策略
        response.headers['Permissions-Policy'] = 'camera=(), microphone=(), geolocation=()'

        # HSTS（仅在 HTTPS 时启用）
        if os.getenv('HTTPS_ENABLED', 'false').lower() == 'true':
            response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'

        return response

    return app


def generate_csrf_token():
    """生成 CSRF 令牌"""
    if not hasattr(g, 'csrf_token'):
        g.csrf_token = secrets.token_hex(32)
    return g.csrf_token


def csrf_protect_api():
    """
    API 端点的 CSRF 保护装饰器
    
    对于使用 API Key 认证的端点，可以豁免 CSRF
    对于 Session 认证的端点，需要验证 CSRF 令牌
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # 如果是 API Key 认证，豁免 CSRF
            api_key = request.headers.get('X-API-Key') or request.headers.get('Token')
            if api_key:
                return f(*args, **kwargs)
            
            # Session 认证需要 CSRF 验证
            if request.method in ['POST', 'PUT', 'DELETE', 'PATCH']:
                token = request.headers.get('X-CSRF-Token') or request.form.get('csrf_token')
                if not token:
                    abort(403, description='CSRF token missing')
                
                # 验证令牌
                if not validate_csrf_token(token):
                    abort(403, description='CSRF token invalid')
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def validate_csrf_token(token):
    """验证 CSRF 令牌"""
    # 简化实现：在实际生产环境中应该使用 Flask-WTF 或 similar
    # 这里仅做基本检查
    if not token or len(token) < 32:
        return False
    return True


def rate_limit_check(max_requests=100, window_seconds=3600):
    """
    简单的速率限制检查（内存实现）
    生产环境应使用 Redis
    """
    # 这里仅作为占位符，实际使用 Flask-Limiter
    pass
