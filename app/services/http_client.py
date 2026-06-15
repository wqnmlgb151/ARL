# -*- coding: utf-8 -*-
"""
ARL HTTP 客户端封装
提供统一的 HTTP 请求接口
"""

import logging
from typing import Dict, Any, Optional
from urllib.parse import urljoin

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class HttpClient:
    """HTTP 客户端"""

    def __init__(self, base_url: str = "", timeout: int = 30, max_retries: int = 3):
        """
        初始化 HTTP 客户端

        Args:
            base_url: 基础 URL
            timeout: 超时时间（秒）
            max_retries: 最大重试次数
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout

        # 创建 session
        self.session = requests.Session()

        # 配置重试策略 - 仅重试幂等操作，避免重复执行写操作
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS", "TRACE"]  # 仅安全/幂等方法
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def _build_url(self, path: str) -> str:
        """构建完整 URL"""
        if path.startswith('http://') or path.startswith('https://'):
            return path
        return f"{self.base_url}/{path.lstrip('/')}"

    def _log_request(self, method: str, url: str, **kwargs) -> None:
        """记录请求日志"""
        logger.debug(f"HTTP {method} {url}")

    def _log_response(self, response: requests.Response, elapsed: float) -> None:
        """记录响应日志"""
        logger.debug(
            f"HTTP {response.status_code} {response.url} - {elapsed:.3f}s"
        )

    def get(self, path: str, params: Optional[Dict[str, Any]] = None,
            headers: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        """
        GET 请求

        Args:
            path: 请求路径
            params: 查询参数
            headers: 请求头
            **kwargs: 其他参数

        Returns:
            Response 对象
        """
        url = self._build_url(path)
        self._log_request("GET", url, params=params)

        response = self.session.get(
            url,
            params=params,
            headers=headers,
            timeout=self.timeout,
            **kwargs
        )

        self._log_response(response, response.elapsed.total_seconds())
        return response

    def post(self, path: str, data: Any = None, json: Any = None,
             headers: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        """
        POST 请求

        Args:
            path: 请求路径
            data: 表单数据
            json: JSON 数据
            headers: 请求头
            **kwargs: 其他参数

        Returns:
            Response 对象
        """
        url = self._build_url(path)
        self._log_request("POST", url)

        response = self.session.post(
            url,
            data=data,
            json=json,
            headers=headers,
            timeout=self.timeout,
            **kwargs
        )

        self._log_response(response, response.elapsed.total_seconds())
        return response

    def put(self, path: str, data: Any = None, json: Any = None,
            headers: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        """
        PUT 请求

        Args:
            path: 请求路径
            data: 表单数据
            json: JSON 数据
            headers: 请求头
            **kwargs: 其他参数

        Returns:
            Response 对象
        """
        url = self._build_url(path)
        self._log_request("PUT", url)

        response = self.session.put(
            url,
            data=data,
            json=json,
            headers=headers,
            timeout=self.timeout,
            **kwargs
        )

        self._log_response(response, response.elapsed.total_seconds())
        return response

    def delete(self, path: str, headers: Optional[Dict[str, str]] = None, **kwargs) -> requests.Response:
        """
        DELETE 请求

        Args:
            path: 请求路径
            headers: 请求头
            **kwargs: 其他参数

        Returns:
            Response 对象
        """
        url = self._build_url(path)
        self._log_request("DELETE", url)

        response = self.session.delete(
            url,
            headers=headers,
            timeout=self.timeout,
            **kwargs
        )

        self._log_response(response, response.elapsed.total_seconds())
        return response

    def request(self, method: str, path: str, **kwargs) -> requests.Response:
        """
        通用请求方法

        Args:
            method: HTTP 方法
            path: 请求路径
            **kwargs: 其他参数

        Returns:
            Response 对象
        """
        url = self._build_url(path)
        self._log_request(method.upper(), url)

        response = self.session.request(
            method.upper(),
            url,
            timeout=self.timeout,
            **kwargs
        )

        self._log_response(response, response.elapsed.total_seconds())
        return response

    def close(self) -> None:
        """关闭 session"""
        self.session.close()


def create_http_client(base_url: str = "", timeout: int = 30, max_retries: int = 3) -> HttpClient:
    """
    创建 HTTP 客户端实例

    Args:
        base_url: 基础 URL
        timeout: 超时时间
        max_retries: 最大重试次数

    Returns:
        HttpClient 实例
    """
    return HttpClient(base_url, timeout, max_retries)
