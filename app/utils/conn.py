import os
import urllib3
import time
import requests
import certifi
import threading
import socket
import ipaddress
from typing import Optional, Dict, Any, List
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.config import Config
from pymongo import MongoClient, ASCENDING, DESCENDING
from requests.exceptions import ReadTimeout
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 安全配置 - 仅在开发环境且明确设置时禁用 SSL 验证
_DISABLE_SSL_VERIFY = os.environ.get('ARL_DISABLE_SSL_VERIFY', 'false').lower() == 'true'

if not _DISABLE_SSL_VERIFY:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 内容处理配置
CONTENT_CHUNK_SIZE = 100 * 1024  # 增大块大小以提高性能
MAX_RESPONSE_SIZE = 100 * 1024 * 1024  # 100MB

# 用户代理
UA = "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36"

# 代理配置（从环境变量读取）
proxies: Dict[str, str] = {}
if os.environ.get('HTTP_PROXY'):
    proxies['http'] = os.environ['HTTP_PROXY']
if os.environ.get('HTTPS_PROXY'):
    proxies['https'] = os.environ['HTTPS_PROXY']

SET_PROXY = False

# SSRF 防护：禁止的 IP 范围（从配置读取，确保一致性）
BLOCKED_IP_RANGES: List[str] = Config.BLACK_IPS or [
    '127.0.0.0/8', '10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16',
    '169.254.0.0/16', '0.0.0.0/8', '::1/128', 'fc00::/7', 'fe80::/10'
]


# ============================================================================
# HTTP 连接池（单例模式）
# ============================================================================

class HTTPClient:
    """HTTP 客户端（单例模式，连接池）"""

    _instance: Optional['HTTPClient'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'HTTPClient':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._session = None
        return cls._instance

    def __init__(self) -> None:
        if self._session is None:
            self._init_session()

    def _init_session(self) -> None:
        """初始化连接池"""
        self._session = requests.Session()

        retry_strategy = Retry(
            total=2,  # 减少重试次数以加速扫描
            backoff_factor=0.5,
            allowed_methods=["HEAD", "GET", "OPTIONS", "TRACE"],
            status_forcelist=[429, 500, 502, 503, 504]
        )

        adapter = HTTPAdapter(
            max_retries=retry_strategy,
            pool_connections=50,  # 增大连接池
            pool_maxsize=100,
            pool_block=False
        )

        self._session.mount("http://", adapter)
        self._session.mount("https://", adapter)
        self._session.headers.update({
            "User-Agent": UA,
            "Cache-Control": "max-age=0",
            "X-Content-Type-Options": "nosniff"
        })

        if Config.PROXY_URL:
            self._session.proxies.update({
                'http': Config.PROXY_URL,
                'https': Config.PROXY_URL
            })

    @property
    def session(self) -> requests.Session:
        """获取底层 Session（高级用法）"""
        return self._session

    def request(self, method: str, url: str, **kwargs) -> requests.Response:
        """发送 HTTP 请求"""
        kwargs.setdefault('timeout', (5, 15))  # 缩短超时时间以加速扫描
        kwargs.setdefault('verify', certifi.where() if not _DISABLE_SSL_VERIFY else False)
        kwargs.setdefault('allow_redirects', True)  # 允许重定向
        kwargs.setdefault('stream', True)

        if 'proxies' not in kwargs and proxies:
            kwargs['proxies'] = proxies

        return self._session.request(method, url, **kwargs)

    def get(self, url: str, **kwargs) -> requests.Response:
        return self.request('get', url, **kwargs)

    def post(self, url: str, **kwargs) -> requests.Response:
        return self.request('post', url, **kwargs)

    def close(self) -> None:
        if self._session:
            self._session.close()


# 全局 HTTP 客户端实例
http_client = HTTPClient()


# ============================================================================
# MongoDB 连接管理（使用新的 DatabaseManager）
# ============================================================================

# 导入新的 DatabaseManager（推荐使用）
from app.database.connection import DatabaseManager, get_collection, get_db, init_db

# 为了向后兼容，保留旧的 ConnMongo 类（将在后续版本中移除）
class ConnMongo:
    """
    MongoDB 连接管理器（已废弃，请使用 DatabaseManager）

    此类仅为向后兼容保留，将在后续版本中移除。
    新代码应使用 app.database.connection.DatabaseManager。
    """

    _instance: Optional['ConnMongo'] = None
    _lock = threading.Lock()

    def __new__(cls) -> 'ConnMongo':
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance.conn = None
                    cls._instance.db = None
        return cls._instance

    def init_app(self, mongo_url: Optional[str] = None, db_name: Optional[str] = None) -> None:
        """初始化数据库连接（委托给 DatabaseManager）"""
        # 使用新的 DatabaseManager 进行初始化
        DatabaseManager.init(mongo_url, db_name)
        self.conn = DatabaseManager.get_client()
        self.db = DatabaseManager.get_db(db_name)

    @property
    def connection(self) -> MongoClient:
        return self.conn

    @property
    def database(self):
        return self.db


def conn_db(collection: str, db_name: Optional[str] = None):
    """
    获取数据库集合（向后兼容）

    新代码推荐使用：from app.database.connection import get_collection
    """
    # 优先使用新的 DatabaseManager
    if DatabaseManager.is_initialized():
        return DatabaseManager.get_collection(collection, db_name)

    # 向后兼容：使用旧的 ConnMongo
    conn = ConnMongo().connection
    if db_name:
        return conn[db_name][collection]
    return conn[Config.MONGO_DB][collection]


# requests/models.py:824
def patch_content(response, timeout=None):
    """Content of the response, in bytes."""
    start_at = time.time()
    if response._content is False:
        # Read the contents.
        if response._content_consumed:
            raise RuntimeError("The content for this response was already consumed")

        if response.status_code == 0 or response.raw is None:
            response._content = None
        else:
            body = b''
            for part in response.iter_content(CONTENT_CHUNK_SIZE):
                body += part
                if timeout is not None and time.time() - start_at >= timeout:
                    raise ReadTimeout(f"patch_content read http response timeout: {timeout}")
            response._content = body
    response._content_consumed = True
    # don't need to release the connection; that's been handled by urllib3
    # since we exhausted the data.
    return response._content


def validate_url(url: str) -> bool:
    """
    验证 URL（包含 SSRF 防护）

    Args:
        url: 要验证的 URL

    Returns:
        URL 是否合法且不指向内网
    """
    import socket
    import logging
    from urllib.parse import urlparse
    from ipaddress import ip_address, ip_network, IPv4Address, IPv6Address

    logger = logging.getLogger(__name__)

    try:
        parsed = urlparse(url)

        # 仅允许 http 和 https 协议
        if parsed.scheme not in ('http', 'https'):
            logger.debug(f"URL blocked - invalid scheme: {url}")
            return False

        # 检查主机名
        hostname = parsed.hostname
        if not hostname:
            logger.debug(f"URL blocked - no hostname: {url}")
            return False

        # SSRF 防护：检查内网 IP
        try:
            # 解析域名获取 IP
            ip_str = socket.gethostbyname(hostname)
            ip = ip_address(ip_str)

            # 检查是否在黑名单中
            for blocked_range in BLOCKED_IP_RANGES:
                try:
                    if ip in ip_network(blocked_range):
                        logger.warning(f"SSRF blocked: {url} -> {ip_str} (range: {blocked_range})")
                        return False
                except (ValueError, TypeError):
                    continue

            logger.debug(f"URL allowed: {url} -> {ip_str}")
            return True

        except socket.gaierror:
            # DNS 解析失败，允许通过（后续请求会失败）
            logger.debug(f"DNS resolution failed for {hostname}, allowing URL: {url}")
            return True
        except ValueError:
            # IP 解析失败
            logger.debug(f"IP parse failed for {hostname}, allowing URL: {url}")
            return True

    except Exception as e:
        logger.debug(f"URL validation failed for {url}: {e}")
        return False


def http_req(url: str, method: str = 'get', use_pool: bool = False, **kwargs) -> requests.Response:
    """
    发送 HTTP 请求

    Args:
        url: 请求 URL
        method: HTTP 方法
        use_pool: 是否使用连接池（默认 False 保持向后兼容）
        **kwargs: 传递给 requests 的参数

    Returns:
        Response 对象

    Raises:
        ValueError: URL 验证失败
    """
    # URL 验证（防止 SSRF）
    if not validate_url(url):
        raise ValueError(f"URL blocked by security policy: {url}")

    if use_pool:
        # 使用连接池客户端
        return http_client.request(method, url, **kwargs)

    # 传统方式（向后兼容）
    kwargs.setdefault('verify', certifi.where() if not _DISABLE_SSL_VERIFY else False)
    kwargs.setdefault('timeout', (5, 15))  # 缩短超时时间以加速扫描
    kwargs.setdefault('allow_redirects', True)  # 允许重定向

    headers = kwargs.get("headers", {})
    headers.setdefault("User-Agent", UA)
    headers.setdefault("Cache-Control", "max-age=0")
    headers.setdefault("X-Content-Type-Options", "nosniff")
    kwargs["headers"] = headers
    kwargs["stream"] = True

    if Config.PROXY_URL:
        proxy_url = Config.PROXY_URL
        proxies['https'] = proxy_url
        proxies['http'] = proxy_url
        kwargs["proxies"] = proxies

    conn = getattr(requests, method)(url, **kwargs)

    timeout = kwargs.get("timeout")
    if isinstance(timeout, tuple) and len(timeout) > 1:
        timeout = timeout[1]

    content = patch_content(conn, timeout)

    if len(content) > MAX_RESPONSE_SIZE:
        raise ValueError(f"Response too large: {len(content)} bytes")

    return conn


# 移除第二个重复的 ConnMongo 类（已合并到 DatabaseManager）
# 保留此注释以标记原有位置