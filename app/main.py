# -*- coding: utf-8 -*-
"""
ARL Web应用主模块
提供REST API接口和Web界面

安全特性：
- 安全响应头
- 请求大小限制
- 安全 Cookie 配置
"""

import os
import logging
from flask import Flask
from flask_restx import Api

from app import routes
from app.middleware import init_security_headers, init_limiter
from app.utils import arl_update, init_logger
from app.utils.sanitizer import MongoSanitizer, sanitize_input
from app.config import Config

logger = logging.getLogger(__name__)

# 创建Flask应用实例
arl_app: Flask = Flask(__name__)

# 安全配置
arl_app.config['BUNDLE_ERRORS'] = True
arl_app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB 最大请求体
arl_app.config['JSON_AS_ASCII'] = False

# 安全 Cookie 配置
arl_app.config['SESSION_COOKIE_SECURE'] = True
arl_app.config['SESSION_COOKIE_HTTPONLY'] = True
arl_app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
arl_app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 小时会话过期




# 配置API认证
authorizations: dict = {
    "ApiKeyAuth": {
        "type": "apiKey",
        "in": "header",
        "name": "Token"
    }
}

# 创建API实例
api: Api = Api(
    arl_app,
    prefix="/api",
    doc="/api/doc",
    title='ARL backend API',
    authorizations=authorizations,
    description='ARL（Asset Reconnaissance Lighthouse）资产侦察灯塔系统',
    security="ApiKeyAuth",
    version="2.6.2"
)

# 注册API命名空间
api.add_namespace(routes.task_ns)
api.add_namespace(routes.site_ns)
api.add_namespace(routes.domain_ns)
api.add_namespace(routes.ip_ns)
api.add_namespace(routes.url_ns)
api.add_namespace(routes.user_ns)
api.add_namespace(routes.image_ns)
api.add_namespace(routes.cert_ns)
api.add_namespace(routes.service_ns)
api.add_namespace(routes.fileleak_ns)
api.add_namespace(routes.export_ns)
api.add_namespace(routes.asset_scope_ns)
api.add_namespace(routes.asset_domain_ns)
api.add_namespace(routes.asset_ip_ns)
api.add_namespace(routes.asset_site_ns)
api.add_namespace(routes.scheduler_ns)
api.add_namespace(routes.poc_ns)
api.add_namespace(routes.vuln_ns)
api.add_namespace(routes.batch_export_ns)
api.add_namespace(routes.policy_ns)
api.add_namespace(routes.npoc_service_ns)
api.add_namespace(routes.task_fofa_ns)
api.add_namespace(routes.console_ns)
api.add_namespace(routes.cip_ns)
api.add_namespace(routes.fingerprint_ns)
api.add_namespace(routes.stat_finger_ns)
api.add_namespace(routes.github_task_ns)
api.add_namespace(routes.github_result_ns)
api.add_namespace(routes.github_scheduler_ns)
api.add_namespace(routes.github_monitor_result_ns)
api.add_namespace(routes.task_schedule_ns)
api.add_namespace(routes.nuclei_result_ns)
api.add_namespace(routes.wih_ns)
api.add_namespace(routes.asset_wih_ns)


def init_app(config_path: str = None) -> None:
    """
    初始化应用
    
    Args:
        config_path: 配置文件路径
    """
    # 加载配置
    if config_path:
        Config.init_app(config_path)
    else:
        Config.init_app()

    # 初始化日志
    init_logger()

    # 认证关闭时发出警告
    if not Config.AUTH:
        logger.warning(Config.AUTH_WARNING)

    # 初始化数据库（带索引优化）
    try:
        from app.utils.conn import init_db
        init_db()
        logger.info("Database initialized with optimized indexes")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")

    # 初始化 Redis（可选）
    try:
        from app.utils.redis_utils import redis_manager
        redis_config = {
            'REDIS_HOST': Config.REDIS_HOST,
            'REDIS_PORT': Config.REDIS_PORT,
            'REDIS_DB': Config.REDIS_DB,
            'REDIS_PASSWORD': Config.REDIS_PASSWORD or None,
        }
        redis_manager.init_app(redis_config)
        logger.info("Redis cache enabled" if redis_manager.enabled else "Redis cache disabled")
    except Exception as e:
        logger.warning(f"Redis initialization failed: {e}")

    # 初始化速率限制（可选）
    if os.getenv('ENABLE_RATE_LIMIT', 'false').lower() == 'true':
        try:
            init_limiter(arl_app)
            logger.info("Rate limiting enabled")
        except Exception as e:
            logger.warning(f"Rate limiter initialization failed: {e}")

    # 执行ARL更新
    arl_update()
    
    # 打印性能优化状态
    _print_optimization_status()


def _print_optimization_status() -> None:
    """打印性能优化组件状态"""
    logger.info("="*50)
    logger.info("Performance Optimization Status:")

    # HTTP 连接池
    try:
        from app.utils.conn import http_client
        logger.info("  [OK] HTTP Connection Pool: enabled")
    except ImportError:
        logger.info("  [--] HTTP Connection Pool: not available")

    # 分布式限流
    try:
        from app.utils.rate_limiter import rate_limiter
        logger.info("  [OK] Distributed Rate Limiter: enabled")
    except ImportError:
        logger.info("  [--] Distributed Rate Limiter: not available")

    # 多级缓存
    try:
        from app.services.cache_service import multi_level_cache
        stats = multi_level_cache.get_stats()
        logger.info(f"  [OK] Multi-level Cache: L1={'enabled' if stats['l1_enabled'] else 'disabled'}, L2={'enabled' if stats['l2_enabled'] else 'disabled'}")
    except ImportError:
        logger.info("  [--] Multi-level Cache: not available")

    # Redis缓存
    try:
        from app.utils.redis_utils import redis_manager
        if redis_manager.enabled:
            logger.info("  [OK] Redis Cache: enabled")
        else:
            logger.info("  [--] Redis Cache: disabled")
    except ImportError:
        logger.info("  [--] Redis Cache: not available")

    logger.info("="*50)


# 注册安全响应头中间件（使用新的 middleware 模块）
init_security_headers(arl_app)

# 注册性能监控中间件
@arl_app.before_request
def before_request():
    """请求前处理：记录请求时间"""
    from flask import g
    import time
    g.request_start_time = time.time()


@arl_app.after_request
def after_request_metrics(response):
    """请求后处理：添加性能头（已迁移到 middleware，保留此函数以兼容旧代码）"""
    from flask import g
    if hasattr(g, 'request_start_time'):
        import time
        elapsed = time.time() - g.request_start_time
        response.headers['X-Response-Time'] = f"{elapsed:.3f}s"

        # 慢请求警告
        if elapsed > 2.0:
            from flask import request
            logger.warning(f"Slow request: {request.method} {request.path} took {elapsed:.3f}s")

    return response


if __name__ == '__main__':
    # Windows 编码修复（仅开发服务器需要）
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

    # 开发环境配置
    debug_mode = os.environ.get('FLASK_DEBUG', 'false').lower() == 'true'
    port = int(os.environ.get('FLASK_PORT', 5018))
    host = os.environ.get('FLASK_HOST', '127.0.0.1')

    init_app()

    if not debug_mode:
        logger.info("Running in production mode")
        arl_app.run(debug=False, port=port, host=host)
    else:
        logger.warning("Running in DEBUG mode - not for production!")
        arl_app.run(debug=True, port=port, host=host)
