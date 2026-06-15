# -*- coding: utf-8 -*-
"""
ARL DNS 解析服务
提供 DNS 查询和解析功能，支持缓存
"""

import logging
from typing import List, Optional, Dict, Any

import dns.resolver

from app.utils.redis_utils import cache_result

logger = logging.getLogger(__name__)


class DnsService:
    """DNS 解析服务"""

    def __init__(self):
        self.resolver = dns.resolver.Resolver()
        self.resolver.timeout = 5
        self.resolver.lifetime = 10

    @cache_result(ttl=3600, key_prefix="dns")
    def query_a(self, domain: str) -> List[str]:
        """
        查询域名的 A 记录

        Args:
            domain: 域名

        Returns:
            IP 地址列表
        """
        ips: List[str] = []

        try:
            answers = self.resolver.resolve(domain, 'A')
            for rdata in answers:
                ip = rdata.address
                if ip != '0.0.0.1':
                    ips.append(ip)
        except dns.resolver.NXDOMAIN:
            logger.debug(f"Domain {domain} does not exist")
        except dns.resolver.NoAnswer:
            logger.debug(f"No A record for {domain}")
        except Exception as e:
            logger.warning(f"DNS query failed for {domain}: {e}")

        return ips

    @cache_result(ttl=3600, key_prefix="dns")
    def query_cname(self, domain: str) -> List[str]:
        """
        查询域名的 CNAME 记录

        Args:
            domain: 域名

        Returns:
            CNAME 列表
        """
        cnames: List[str] = []

        try:
            answers = self.resolver.resolve(domain, 'CNAME')
            for rdata in answers:
                cname = str(rdata.target).strip(".").lower()
                cnames.append(cname)
        except dns.resolver.NoAnswer:
            logger.debug(f"No CNAME record for {domain}")
        except Exception as e:
            logger.warning(f"CNAME query failed for {domain}: {e}")

        return cnames

    @cache_result(ttl=7200, key_prefix="dns")
    def query_mx(self, domain: str) -> List[str]:
        """
        查询域名的 MX 记录

        Args:
            domain: 域名

        Returns:
            MX 记录列表
        """
        mx_records: List[str] = []

        try:
            answers = self.resolver.resolve(domain, 'MX')
            for rdata in answers:
                mx = str(rdata.exchange).strip(".").lower()
                mx_records.append(mx)
        except dns.resolver.NoAnswer:
            logger.debug(f"No MX record for {domain}")
        except Exception as e:
            logger.warning(f"MX query failed for {domain}: {e}")

        return mx_records

    @cache_result(ttl=7200, key_prefix="dns")
    def query_ns(self, domain: str) -> List[str]:
        """
        查询域名的 NS 记录

        Args:
            domain: 域名

        Returns:
            NS 记录列表
        """
        ns_records: List[str] = []

        try:
            answers = self.resolver.resolve(domain, 'NS')
            for rdata in answers:
                ns = str(rdata.target).strip(".").lower()
                ns_records.append(ns)
        except dns.resolver.NoAnswer:
            logger.debug(f"No NS record for {domain}")
        except Exception as e:
            logger.warning(f"NS query failed for {domain}: {e}")

        return ns_records

    @cache_result(ttl=3600, key_prefix="dns")
    def query_txt(self, domain: str) -> List[str]:
        """
        查询域名的 TXT 记录

        Args:
            domain: 域名

        Returns:
            TXT 记录列表
        """
        txt_records: List[str] = []

        try:
            answers = self.resolver.resolve(domain, 'TXT')
            for rdata in answers:
                txt = str(rdata)
                txt_records.append(txt)
        except dns.resolver.NoAnswer:
            logger.debug(f"No TXT record for {domain}")
        except Exception as e:
            logger.warning(f"TXT query failed for {domain}: {e}")

        return txt_records

    def batch_query(self, domains: List[str], record_type: str = 'A',
                    max_workers: int = 10) -> Dict[str, List[str]]:
        """
        批量查询多个域名（并行执行）

        Args:
            domains: 域名列表
            record_type: 记录类型 (A, CNAME, MX, NS, TXT)
            max_workers: 最大并发线程数

        Returns:
            域名到记录的映射
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed

        results: Dict[str, List[str]] = {}

        query_func = {
            'A': self.query_a,
            'CNAME': self.query_cname,
            'MX': self.query_mx,
            'NS': self.query_ns,
            'TXT': self.query_txt,
        }.get(record_type.upper())

        if not query_func:
            logger.error(f"Unsupported record type: {record_type}")
            return results

        # 并行查询以提高吞吐量
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_domain = {
                executor.submit(query_func, domain): domain
                for domain in domains
            }
            for future in as_completed(future_to_domain):
                domain = future_to_domain[future]
                try:
                    results[domain] = future.result()
                except Exception as e:
                    logger.warning(f"Batch query failed for {domain}: {e}")
                    results[domain] = []

        return results

    def clear_cache(self, domain: Optional[str] = None) -> None:
        """
        清除 DNS 缓存

        Args:
            domain: 指定域名，None 表示清除所有
        """
        from app.utils.redis_utils import invalidate_cache

        if domain:
            invalidate_cache("dns", domain)
        else:
            invalidate_cache("dns")


# 全局 DNS 服务实例
dns_service = DnsService()
