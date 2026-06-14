# -*- coding: utf-8 -*-
"""
ARL 网络工具模块
提供域名解析、IP 获取等网络相关功能
"""

import re
import logging
from typing import List, Dict, Optional

import dns.resolver
from tld import get_tld

logger = logging.getLogger(__name__)


def domain_parsed(domain: str, fail_silently: bool = True) -> Optional[Dict[str, str]]:
    """
    解析域名

    Args:
        domain: 域名
        fail_silently: 失败时是否静默返回 None

    Returns:
        解析结果字典，包含 domain, fld, subdomain 等
    """
    try:
        # 清理域名
        domain = domain.strip().lower()
        if domain.startswith(('http://', 'https://')):
            from urllib.parse import urlparse
            parsed = urlparse(domain)
            domain = parsed.hostname or domain

        # 使用 tld 库解析
        res = get_tld(domain, as_object=True)
        return {
            'domain': domain,
            'fld': f"{res.domain}.{res.suffix}",
            'subdomain': res.subdomain,
            'suffix': res.suffix,
        }
    except Exception as e:
        if not fail_silently:
            logger.warning(f"Domain parsing failed for {domain}: {e}")
        return None


def get_ip(domain: str, log_flag: bool = True) -> List[str]:
    """
    获取域名的 IP 地址

    Args:
        domain: 域名
        log_flag: 是否记录日志

    Returns:
        IP 地址列表
    """
    try:
        # 清理域名
        domain = domain.strip().lower()
        if domain.startswith(('http://', 'https://')):
            from urllib.parse import urlparse
            parsed = urlparse(domain)
            domain = parsed.hostname or domain

        # DNS A 记录查询
        answers = dns.resolver.resolve(domain, 'A')
        ips = [str(rdata) for rdata in answers]

        if log_flag:
            logger.debug(f"Resolved {domain} -> {ips}")

        return ips
    except Exception as e:
        if log_flag:
            logger.warning(f"DNS resolution failed for {domain}: {e}")
        return []


def get_fld(d: str) -> Optional[str]:
    """
    获取域名的主域（二级域名）

    Args:
        d: 域名

    Returns:
        主域名（如 example.com）
    """
    res = domain_parsed(d)
    if res:
        return res["fld"]
    return None


def gen_filename(site: str) -> str:
    """
    根据 URL 生成文件名

    Args:
        site: URL

    Returns:
        安全的文件名
    """
    filename = site.replace('://', '_')
    return re.sub(r'[^\w\-_\. ]', '_', filename)
