# -*- coding: utf-8 -*-
"""
ARL API 网关
提供统一的 API 入口、请求路由、认证和限流
"""

import time
import logging
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from functools import wraps

from flask import Flask, request, jsonify, g

logger = logging.getLogger(__name__)


@dataclass
class RequestContext:
    """请求上下文"""
    request_id: str
    method: str
    path: str
    headers: Dict[str, str]
    params: Dict[str, Any]
    body: Any
    user: Optional[Dict[str, Any]] = None
    start_time: float = 0.0

    def __post_init__(self):
        if self.start_time == 0.0:
            self.start_time = time.time()

    def elapsed_time(self) -> float:
        """获取请求耗时"""
        return time.time() - self.start_time


@dataclass
class RateLimitConfig:
    """限流配置"""
    enabled: bool = True
    requests_per_minute: int = 60
    burst_size: int = 10


@dataclass
class AuthConfig:
    """认证配置"""
    enabled: bool = True
    api_key_header: str = "Token"
    excluded_paths: List[str] = field(default_factory=lambda: ["/api/doc", "/health"])


class ResponseBuilder:
    """响应构建器"""

    @staticmethod
    def success(data: Any = None, message: str = "success", code: int = 200) -> Dict[str, Any]:
        """构建成功响应"""
        return {
            "code": code,
            "message": message,
            "data": data,
            "success": True
        }

    @staticmethod
    def error(message: str = "error", code: int = 400, data: Any = None) -> Dict[str, Any]:
        """构建错误响应"""
        return {
            "code": code,
            "message": message,
            "data": data,
            "success": False
        }

    @staticmethod
    def unauthorized(message: str = "Unauthorized") -> Dict[str, Any]:
        """构建未授权响应"""
        return ResponseBuilder.error(message, code=401)

    @staticmethod
    def forbidden(message: str = "Forbidden") -> Dict[str, Any]:
        """构建禁止访问响应"""
        return ResponseBuilder.error(message, code=403)

    @staticmethod
    def not_found(message: str = "Not Found") -> Dict[str, Any]:
        """构建未找到响应"""
        return ResponseBuilder.error(message, code=404)

    @staticmethod
    def too_many_requests(message: str = "Too Many Requests") -> Dict[str, Any]:
        """构建限流响应"""
        return ResponseBuilder.error(message, code=429)

    @staticmethod
    def internal_error(message: str = "Internal Server Error") -> Dict[str, Any]:
        """构建服务器错误响应"""
        return ResponseBuilder.error(message, code=500)


class ApiGateway:
    """API 网关"""

    def __init__(self, app: Optional[Flask] = None):
        self.app = app
        self.rate_limit_config = RateLimitConfig()
        self.auth_config = AuthConfig()
        self._request_counts: Dict[str, List[float]] = {}
        self._middleware: List[Callable] = []

        if app:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """初始化应用"""
        self.app = app

        # 注册请求钩子
        app.before_request(self._before_request)
        app.after_request(self._after_request)
        app.errorhandler(404)(self._handle_404)
        app.errorhandler(500)(self._handle_500)

        logger.info("API Gateway initialized")

    def _before_request(self) -> Optional[Any]:
        """请求前处理"""
        # 创建请求上下文
        context = RequestContext(
            request_id=request.headers.get('X-Request-ID', str(time.time())),
            method=request.method,
            path=request.path,
            headers=dict(request.headers),
            params=dict(request.args),
            body=request.get_json(silent=True)
        )
        g.request_context = context

        # 跳过特定路径
        if self._should_skip_path(context.path):
            return None

        # 认证检查
        if self.auth_config.enabled:
            auth_result = self._check_auth(context)
            if auth_result:
                return auth_result

        # 限流检查
        if self.rate_limit_config.enabled:
            rate_result = self._check_rate_limit(context)
            if rate_result:
                return rate_result

        # 执行中间件
        for middleware in self._middleware:
            result = middleware(context)
            if result:
                return result

        return None

    def _after_request(self, response):
        """请求后处理"""
        # 添加响应头
        response.headers['X-Request-ID'] = getattr(g, 'request_context', None) and g.request_context.request_id or 'unknown'
        response.headers['X-Response-Time'] = str(
            getattr(g, 'request_context', None) and g.request_context.elapsed_time() or 0
        )

        # 记录日志
        if hasattr(g, 'request_context'):
            logger.info(
                f"{g.request_context.method} {g.request_context.path} - "
                f"{response.status_code} - {g.request_context.elapsed_time():.3f}s"
            )

        return response

    def _should_skip_path(self, path: str) -> bool:
        """检查是否应跳过路径"""
        for excluded in self.auth_config.excluded_paths:
            if path.startswith(excluded):
                return True
        return False

    def _check_auth(self, context: RequestContext) -> Optional[Any]:
        """
        检查认证

        验证 API Key 是否有效，防止未授权访问
        """
        api_key = context.headers.get(self.auth_config.api_key_header)

        if not api_key:
            # 记录认证失败
            logger.warning(f"Missing API key from {request.remote_addr}")
            return jsonify(ResponseBuilder.unauthorized("Missing API key"))

        # 验证 API Key
        if not self._validate_api_key(api_key):
            logger.warning(f"Invalid API key from {request.remote_addr}")
            return jsonify(ResponseBuilder.unauthorized("Invalid API key"))

        return None

    def _validate_api_key(self, api_key: str) -> bool:
        """
        验证 API Key 是否有效

        Args:
            api_key: API Key

        Returns:
            是否有效
        """
        # 1. 首先检查是否匹配配置的 API Key
        if api_key == Config.API_KEY:
            return True

        # 2. 然后检查数据库中的用户 Token
        try:
            from app.utils.conn import conn_db
            user = conn_db('user').find_one({"token": api_key})
            if user:
                # 检查 Token 是否过期
                expires_at = user.get('expires_at')
                if expires_at:
                    from datetime import datetime
                    if datetime.utcnow() > expires_at:
                        return False
                return True
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception(f"Error in {__name__}: {e}")
            # Log full traceback for API key validation errors - security critical
            logger.error(f"Error validating API key: {e}", exc_info=True)

        return False

    def _check_rate_limit(self, context: RequestContext) -> Optional[Any]:
        """检查限流（带定期清理防止内存泄漏）"""
        client_ip = request.remote_addr
        current_time = time.time()
        window = 60  # 1 分钟窗口

        # 初始化或清理过期记录
        if client_ip not in self._request_counts:
            self._request_counts[client_ip] = []

        # 清理过期的请求记录
        self._request_counts[client_ip] = [
            t for t in self._request_counts[client_ip]
            if current_time - t < window
        ]

        # 检查是否超过限制
        if len(self._request_counts[client_ip]) >= self.rate_limit_config.requests_per_minute:
            return jsonify(ResponseBuilder.too_many_requests())

        # 记录请求
        self._request_counts[client_ip].append(current_time)

        # 定期清理过期的 IP 记录（防止内存泄漏）
        if len(self._request_counts) > 10000:
            self._cleanup_old_ips(current_time, window)

        return None

    def _cleanup_old_ips(self, current_time: float, window: int) -> None:
        """清理长时间无活动的 IP 记录"""
        expired_ips = [
            ip for ip, times in self._request_counts.items()
            if not times or current_time - max(times) > window * 2
        ]
        for ip in expired_ips:
            del self._request_counts[ip]
        if expired_ips:
            logger.info(f"Rate limiter cleaned up {len(expired_ips)} expired IPs")

    def _handle_404(self, error):
        """处理 404 错误"""
        return jsonify(ResponseBuilder.not_found()), 404

    def _handle_500(self, error):
        """
        处理 500 错误

        安全说明：向用户返回通用错误信息，详细错误仅记录在服务器日志中
        """
        # 记录详细错误信息（包含堆栈跟踪）
        logger.error(f"Internal server error: {error}", exc_info=True)

        # 返回通用错误信息给用户（不泄露内部细节）
        return jsonify({
            "code": 500,
            "message": "An internal error occurred. Please try again later.",
            "success": False
        }), 500

    def add_middleware(self, middleware: Callable) -> None:
        """添加中间件"""
        self._middleware.append(middleware)

    def set_rate_limit(self, config: RateLimitConfig) -> None:
        """设置限流配置"""
        self.rate_limit_config = config

    def set_auth(self, config: AuthConfig) -> None:
        """设置认证配置"""
        self.auth_config = config


def require_api_key(f: Callable) -> Callable:
    """API Key 认证装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('Token')

        if not api_key:
            return jsonify(ResponseBuilder.unauthorized("Missing API key"))

        # TODO: 验证 API Key

        return f(*args, **kwargs)
    return decorated


def rate_limit(requests_per_minute: int = 60) -> Callable:
    """限流装饰器"""
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args, **kwargs):
            # TODO: 实现更细粒度的限流
            return f(*args, **kwargs)
        return decorated
    return decorator
