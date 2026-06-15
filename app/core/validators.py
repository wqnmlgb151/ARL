# -*- coding: utf-8 -*-
"""
ARL输入验证器
提供统一的输入验证和清理功能，防止注入攻击
"""

import re
from typing import Optional
from urllib.parse import urlparse

from app.core.exceptions import ValidationException

# HTML转义映射表（常量，避免重复创建）
_HTML_ESCAPE_TABLE = str.maketrans({
    "&": "&amp;",
    '"': "&quot;",
    "'": "&#x27;",
    ">": "&gt;",
    "<": "&lt;"
})


def validate_ip(ip: str) -> bool:
    """
    验证IP地址格式

    Args:
        ip: IP地址字符串

    Returns:
        是否有效

    Raises:
        ValidationException: IP格式无效时抛出异常
    """
    import ipaddress

    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        raise ValidationException(f"Invalid IP address format: {ip}", field="ip")


def validate_ip_range(ip_range: str) -> bool:
    """
    验证IP范围格式（支持CIDR和范围表示）

    Args:
        ip_range: IP范围字符串（如192.168.1.0/24 或 192.168.1.1-192.168.1.100）

    Returns:
        是否有效

    Raises:
        ValidationException: IP范围格式无效时抛出异常
    """
    import ipaddress

    # 尝试CIDR格式
    try:
        ipaddress.ip_network(ip_range, strict=False)
        return True
    except ValueError:
        pass

    # 尝试范围格式
    if '-' in ip_range:
        parts = ip_range.split('-')
        if len(parts) == 2:
            try:
                start_ip = ipaddress.ip_address(parts[0].strip())
                end_ip = ipaddress.ip_address(parts[1].strip())
                if start_ip <= end_ip:
                    return True
            except ValueError:
                pass

    raise ValidationException(f"Invalid IP range format: {ip_range}", field='ip_range')


def validate_cidr(cidr: str) -> bool:
    """
    验证CIDR格式

    Args:
        cidr: CIDR字符串（如192.168.1.0/24）

    Returns:
        是否有效

    Raises:
        ValidationException: CIDR格式无效时抛出异常
    """
    import ipaddress

    try:
        ipaddress.ip_network(cidr, strict=True)
        return True
    except ValueError:
        raise ValidationException(f"Invalid CIDR format: {cidr}", field='cidr')


def validate_domain(domain: str) -> bool:
    """
    验证域名格式

    Args:
        domain: 域名

    Returns:
        是否有效

    Raises:
        ValidationException: 域名格式无效时抛出异常
    """
    from app.utils.domain import is_valid_domain

    if not is_valid_domain(domain):
        raise ValidationException(f"Invalid domain format: {domain}", field='domain')
    return True


def validate_url(url: str) -> bool:
    """
    验证URL格式

    Args:
        url: URL字符串

    Returns:
        是否有效

    Raises:
        ValidationException: URL格式无效时抛出异常
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ('http', 'https'):
            raise ValidationException(f"Invalid URL scheme: {parsed.scheme}", field='url')
        if not parsed.hostname:
            raise ValidationException(f"Invalid URL: missing hostname", field='url')
        return True
    except Exception as e:
        raise ValidationException(f"Invalid URL format: {url}, error: {str(e)}", field='url')


def validate_port(port: int) -> bool:
    """
    验证端口号

    Args:
        port: 端口号

    Returns:
        是否有效

    Raises:
        ValidationException: 端口号无效时抛出异常
    """
    if not isinstance(port, int) or port < 1 or port > 65535:
        raise ValidationException(f"Invalid port number: {port} (must be 1-65535)", field='port')
    return True


def validate_port_range(port_range: str) -> bool:
    """
    验证端口范围格式

    Args:
        port_range: 端口范围字符串（如80,443 或 1-1024）

    Returns:
        是否有效

    Raises:
        ValidationException: 端口范围格式无效时抛出异常
    """
    # 支持格式：80,443 或 1-1024 或 80,443,1000-2000
    parts = port_range.split(',')
    for part in parts:
        part = part.strip()
        if '-' in part:
            range_parts = part.split('-')
            if len(range_parts) != 2:
                raise ValidationException(f"Invalid port range format: {port_range}", field='port_range')
            try:
                start = int(range_parts[0].strip())
                end = int(range_parts[1].strip())
                if start < 1 or end > 65535 or start > end:
                    raise ValidationException(f"Invalid port range: {port_range}", field='port_range')
            except ValueError:
                raise ValidationException(f"Invalid port range: {port_range}", field='port_range')
        else:
            try:
                port = int(part)
                if port < 1 or port > 65535:
                    raise ValidationException(f"Invalid port: {port}", field='port_range')
            except ValueError:
                raise ValidationException(f"Invalid port range: {port_range}", field='port_range')
    return True


def validate_object_id(oid: str) -> bool:
    """
    验证MongoDB ObjectId格式

    Args:
        oid: ObjectId字符串

    Returns:
        是否有效

    Raises:
        ValidationException: ObjectId格式无效时抛出异常
    """
    from bson import ObjectId
    from bson.errors import InvalidId

    try:
        ObjectId(oid)
        return True
    except InvalidId:
        raise ValidationException(f"Invalid ObjectId format: {oid}", field='object_id')


def validate_task_type(task_type: str) -> bool:
    """
    验证任务类型

    Args:
        task_type: 任务类型字符串

    Returns:
        是否有效

    Raises:
        ValidationException: 任务类型无效时抛出异常
    """
    from app.core.types import TaskType

    valid_types = [t.value for t in TaskType]
    if task_type not in valid_types:
        raise ValidationException(f"Invalid task type: {task_type}. Must be one of: {valid_types}", field='task_type')
    return True


def sanitize_input(text: str, max_length: int = 1000) -> str:
    """
    清理用户输入（防止XSS和注入攻击）

    Args:
        text: 输入文本
        max_length: 最大长度（默认1000）

    Returns:
        清理后的文本
    """
    if not text:
        return ""

    # 移除控制字符
    text = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', text)

    # 转义HTML特殊字符
    html_escape_table = {
        "&": "&amp;",
        '"': "&quot;",
        "'": "&#x27;",
        ">": "&gt;",
        "<": "&lt;",
    }
    for char, escape in html_escape_table.items():
        text = text.replace(char, escape)

    # 截断过长输入
    if len(text) > max_length:
        text = text[:max_length]

    return text.strip()


def validate_search_query(query: str) -> bool:
    """
    验证搜索查询

    Args:
        query: 搜索查询字符串

    Returns:
        是否有效

    Raises:
        ValidationException: 查询格式无效时抛出异常
    """
    if not query or not query.strip():
        raise ValidationException("Search query cannot be empty", field='query')

    if len(query) > 200:
        raise ValidationException("Search query too long (max 200 characters)", field='query')

    # 防止正则注入
    dangerous_patterns = ['.*', '.+', '$', '^', '(?']
    for pattern in dangerous_patterns:
        if pattern in query:
            raise ValidationException(f"Invalid characters in search query", field='query')

    return True


# 导出所有验证器
__all__ = [
    'validate_ip',
    'validate_ip_range',
    'validate_cidr',
    'validate_domain',
    'validate_url',
    'validate_port',
    'validate_port_range',
    'validate_object_id',
    'validate_task_type',
    'sanitize_input',
    'validate_search_query'
]
