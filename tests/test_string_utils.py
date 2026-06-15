# -*- coding: utf-8 -*-
"""
字符串工具模块单元测试
"""

import pytest

from app.utils.string_utils import (
    truncate_string, truncate_string_middle, gen_md5, gen_sha256,
    clean_string, normalize_whitespace, extract_numbers,
    is_empty_or_whitespace, safe_strip, remove_prefix, remove_suffix,
    DEFAULT_TRUNCATE_LENGTH, DEFAULT_TRUNCATE_SUFFIX
)


class TestTruncateString:
    """测试 truncate_string 函数"""

    def test_short_string(self):
        """测试短字符串不截断"""
        assert truncate_string("hello") == "hello"

    def test_exact_length(self):
        """测试刚好等于最大长度"""
        s = "a" * DEFAULT_TRUNCATE_LENGTH
        assert truncate_string(s) == s

    def test_long_string(self):
        """测试长字符串截断"""
        s = "a" * (DEFAULT_TRUNCATE_LENGTH + 10)
        result = truncate_string(s)
        assert len(result) == DEFAULT_TRUNCATE_LENGTH + len(DEFAULT_TRUNCATE_SUFFIX)
        assert result.endswith(DEFAULT_TRUNCATE_SUFFIX)

    def test_custom_max_length(self):
        """测试自定义最大长度"""
        s = "hello world"
        result = truncate_string(s, max_length=5)
        assert result == "hello..."

    def test_custom_suffix(self):
        """测试自定义后缀"""
        s = "hello world"
        result = truncate_string(s, max_length=5, suffix="***")
        assert result == "hello***"


class TestTruncateStringMiddle:
    """测试 truncate_string_middle 函数"""

    def test_short_string(self):
        """测试短字符串不截断"""
        assert truncate_string_middle("hello") == "hello"

    def test_long_string(self):
        """测试长字符串中间截断"""
        s = "abcdefghijklmnopqrstuvwxyz"
        result = truncate_string_middle(s, max_length=15)
        assert len(result) == 15
        assert "..." in result

    def test_preserves_head_and_tail(self):
        """测试保留首尾"""
        s = "abcdefghijklmnopqrstuvwxyz"
        result = truncate_string_middle(s, max_length=15)
        # 前半部分7个字符 + ... + 后半部分5个字符 = 15
        assert result.startswith("abcdefg")
        assert result.endswith("vwxyz")


class TestGenMd5:
    """测试 gen_md5 函数"""

    def test_md5_hash(self):
        """测试MD5哈希生成"""
        result = gen_md5("hello")
        assert result == "5d41402abc4b2a76b9719d911017c592"

    def test_md5_empty_string(self):
        """测试空字符串"""
        result = gen_md5("")
        assert result == "d41d8cd98f00b204e9800998ecf8427e"


class TestGenSha256:
    """测试 gen_sha256 函数"""

    def test_sha256_hash(self):
        """测试SHA256哈希生成"""
        result = gen_sha256("hello")
        assert result == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"


class TestCleanString:
    """测试 clean_string 函数"""

    def test_clean_special_chars(self):
        """测试清理特殊字符"""
        result = clean_string("hello@world#test")
        assert result == "hello_world_test"

    def test_allow_spaces(self):
        """测试允许空格"""
        result = clean_string("hello world", allow_spaces=True)
        assert result == "hello world"

    def test_remove_spaces(self):
        """测试移除空格"""
        result = clean_string("hello world", allow_spaces=False)
        assert result == "hello_world"


class TestNormalizeWhitespace:
    """测试 normalize_whitespace 函数"""

    def test_multiple_spaces(self):
        """测试多个空格"""
        result = normalize_whitespace("hello    world")
        assert result == "hello world"

    def test_tabs_and_newlines(self):
        """测试制表符和换行符"""
        result = normalize_whitespace("hello\t\nworld")
        assert result == "hello world"

    def test_leading_trailing(self):
        """测试首尾空白"""
        result = normalize_whitespace("  hello world  ")
        assert result == "hello world"


class TestExtractNumbers:
    """测试 extract_numbers 函数"""

    def test_extract_numbers(self):
        """测试提取数字"""
        result = extract_numbers("abc123def456")
        assert result == ["123", "456"]

    def test_no_numbers(self):
        """测试无数字"""
        result = extract_numbers("abcdef")
        assert result == []


class TestIsEmptyOrWhitespace:
    """测试 is_empty_or_whitespace 函数"""

    def test_none(self):
        """测试None"""
        assert is_empty_or_whitespace(None) is True

    def test_empty_string(self):
        """测试空字符串"""
        assert is_empty_or_whitespace("") is True

    def test_whitespace(self):
        """测试空白字符串"""
        assert is_empty_or_whitespace("   ") is True

    def test_non_empty(self):
        """测试非空字符串"""
        assert is_empty_or_whitespace("hello") is False


class TestSafeStrip:
    """测试 safe_strip 函数"""

    def test_strip_whitespace(self):
        """测试去除空白"""
        result = safe_strip("  hello  ")
        assert result == "hello"

    def test_none_input(self):
        """测试None输入"""
        result = safe_strip(None)
        assert result == ""


class TestRemovePrefix:
    """测试 remove_prefix 函数"""

    def test_remove_prefix(self):
        """测试移除前缀"""
        result = remove_prefix("hello_world", "hello_")
        assert result == "world"

    def test_no_prefix(self):
        """测试无前缀"""
        result = remove_prefix("hello_world", "test_")
        assert result == "hello_world"


class TestRemoveSuffix:
    """测试 remove_suffix 函数"""

    def test_remove_suffix(self):
        """测试移除后缀"""
        result = remove_suffix("hello_world", "_world")
        assert result == "hello"

    def test_no_suffix(self):
        """测试无后缀"""
        result = remove_suffix("hello_world", "_test")
        assert result == "hello_world"
