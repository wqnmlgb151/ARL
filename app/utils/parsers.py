# -*- coding: utf-8 -*-
"""
ARL 解析工具模块
提供域名、URL、证书等解析功能
"""

import re
import logging
from typing import Dict, Any, Optional, Union

logger = logging.getLogger(__name__)


def build_ret(error: Union[str, Dict[str, Any]], data: Any) -> Dict[str, Any]:
    """
    构建 API 响应

    Args:
        error: 错误信息（字符串或字典）
        data: 响应数据

    Returns:
        标准响应字典
    """
    if isinstance(error, str):
        error = {
            "message": error,
            "code": 999,
        }

    ret: Dict[str, Any] = {}
    ret.update(error)
    ret["data"] = data
    msg = error["message"]

    if error["code"] != 200:
        for k, v in data.items():
            if k.endswith("id"):
                continue
            if not v:
                continue
            if isinstance(v, str):
                msg += f" {k}:{v}"

    ret["message"] = msg
    return ret


def get_domain(domain: str) -> Optional[str]:
    """
    从 URL 或域名中提取主域名

    Args:
        domain: URL 或域名

    Returns:
        主域名（如 example.com）
    """
    from app.utils.network import get_fld
    return get_fld(domain)


def get_ip_from_domain(domain: str) -> list:
    """
    从域名获取 IP 地址

    Args:
        domain: 域名

    Returns:
        IP 地址列表
    """
    from app.utils.network import get_ip
    return get_ip(domain)


# 导入原有的 domain.py 和 ip.py 中的函数（向后兼容）
from app.utils.domain import (
    check_domain_black,
    is_forbidden_domain,
    is_valid_domain,
    is_valid_fuzz_domain,
    is_in_scope,
    is_in_scopes,
    cut_first_name,
)

from app.utils.ip import (
    is_vaild_ip_target,
    transfer_ip_scope,
    not_in_black_ips,
    get_ip_asn,
    get_ip_city,
    get_ip_type,
    ip_in_scope,
)
