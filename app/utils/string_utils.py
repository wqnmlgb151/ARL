# -*- coding: utf-8 -*-
"""
ARL字符串处理工具模块
提供统一的字符串处理函数，避免代码重复
"""

import re
import hashlib
from typing import Optional


# 默认截断长度
DEFAULT_TRUNCATE_LENGTH = 30

# 默认截断后缀
DEFAULT_TRUNCATE_SUFFIX = "..."


def truncate_string(s: str, max_length: int = DEFAULT_TRUNCATE_LENGTH,
                   suffix: str = DEFAULT_TRUNCATE_SUFFIX) -> str:
    """
    截断字符串

    Args:
        s: 输入字符串
        max_length: 最大长度，默认30
        suffix: 截断后缀，默认"..."

    Returns:
        截断后的字符串
    """
    if len(s) <= max_length:
        return s
    return s[:max_length] + suffix


def truncate_string_middle(s: str, max_length: int = DEFAULT_TRUNCATE_LENGTH,
                           separator: str = "...") -> str:
    """
    从中间截断字符串（保留首尾部分）

    Args:
        s: 输入字符串
        max_length: 最大长度，默认30
        separator: 分隔符，默认"..."

    Returns:
        截断后的字符串
    """
    if len(s) <= max_length:
        return s

    # 计算保留的字符数（减去分隔符长度）
    keep_length = max_length - len(separator)
    if keep_length <= 0:
        return s[:max_length]

    # 前半部分和后半部分
    head_length = keep_length // 2
    tail_length = keep_length - head_length

    return s[:head_length] + separator + s[-tail_length:]


def gen_md5(s: str) -> str:
    """
    生成MD5哈希

    Args:
        s: 输入字符串

    Returns:
        MD5哈希值
    """
    return hashlib.md5(s.encode()).hexdigest()


def gen_sha256(s: str) -> str:
    """
    生成SHA256哈希

    Args:
        s: 输入字符串

    Returns:
        SHA256哈希值
    """
    return hashlib.sha256(s.encode()).hexdigest()


def clean_string(s: str, allow_spaces: bool = False) -> str:
    """
    清理字符串，移除特殊字符

    Args:
        s: 输入字符串
        allow_spaces: 是否允许空格

    Returns:
        清理后的字符串
    """
    if allow_spaces:
        return re.sub(r'[^\w\-_\. ]', '_', s)
    return re.sub(r'[^\w\-_\.]', '_', s)


def normalize_whitespace(s: str) -> str:
    """
    规范化空白字符（多个空格/制表符/换行符转为单个空格）

    Args:
        s: 输入字符串

    Returns:
        规范化后的字符串
    """
    return re.sub(r'\s+', ' ', s).strip()


def extract_numbers(s: str) -> list:
    """
    从字符串中提取所有数字

    Args:
        s: 输入字符串

    Returns:
        数字字符串列表
    """
    return re.findall(r'\d+', s)


def is_empty_or_whitespace(s: Optional[str]) -> bool:
    """
    检查字符串是否为空或仅包含空白字符

    Args:
        s: 输入字符串

    Returns:
        是否为空或空白
    """
    if s is None:
        return True
    return not s.strip()


def safe_strip(s: Optional[str]) -> str:
    """
    安全地去除字符串两端空白

    Args:
        s: 输入字符串

    Returns:
        去除空白后的字符串，None返回空字符串
    """
    if s is None:
        return ""
    return s.strip()


def remove_prefix(s: str, prefix: str) -> str:
    """
    移除字符串前缀（Python 3.9+兼容）

    Args:
        s: 输入字符串
        prefix: 要移除的前缀

    Returns:
        移除前缀后的字符串
    """
    if s.startswith(prefix):
        return s[len(prefix):]
    return s


def remove_suffix(s: str, suffix: str) -> str:
    """
    移除字符串后缀（Python 3.9+兼容）

    Args:
        s: 输入字符串
        suffix: 要移除的后缀

    Returns:
        移除后缀后的字符串
    """
    if s.endswith(suffix):
        return s[:-len(suffix)]
    return s
