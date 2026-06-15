# -*- coding: utf-8 -*-
"""
输入验证器测试
"""
import pytest
from unittest.mock import patch
from app.core.validators import (
    validate_domain,
    validate_ip,
    validate_url,
    validate_port,
    sanitize_input,
    validate_task_type,
)
from app.core.exceptions import ValidationException


class TestValidateDomain:
    """域名验证测试"""

    def test_valid_domains(self):
        """测试有效域名"""
        valid_domains = [
            "example.com",
            "sub.example.com",
            "example.co.uk",
            "test-domain.com",
            "123.123.123.com",
            "xn--nxasmq6b.com",  # IDN域名
        ]

        with patch('app.utils.domain.is_valid_domain', return_value=True):
            for domain in valid_domains:
                result = validate_domain(domain)
                assert result is True, f"域名 {domain} 应该验证通过"

    def test_invalid_domains(self):
        """测试无效域名"""
        invalid_domains = [
            "",
            "   ",
            "example",  # 没有TLD
            "example.",  # 以点结尾
            ".example.com",  # 以点开头
            "exam..ple.com",  # 双点
            "example.com:80",  # 包含端口
            "http://example.com",  # 包含协议
            "user@example.com",  # 邮箱格式
        ]

        with patch('app.utils.domain.is_valid_domain', return_value=False):
            for domain in invalid_domains:
                with pytest.raises(ValidationException):
                    validate_domain(domain)

    def test_domain_injection_attempts(self):
        """测试域名注入尝试"""
        malicious_inputs = [
            "example.com; rm -rf /",
            "example.com && cat /etc/passwd",
            "$(whoami).example.com",
            "{{7*7}}.example.com",
        ]

        with patch('app.utils.domain.is_valid_domain', return_value=False):
            for malicious in malicious_inputs:
                with pytest.raises(ValidationException):
                    validate_domain(malicious)


class TestValidateIP:
    """IP地址验证测试"""

    def test_valid_ipv4(self):
        """测试有效IPv4地址"""
        valid_ips = [
            "192.168.1.1",
            "10.0.0.1",
            "172.16.0.1",
            "8.8.8.8",
            "255.255.255.255",
            "0.0.0.0",
        ]

        for ip in valid_ips:
            result = validate_ip(ip)
            assert result is not None, f"IP {ip} 应该验证通过"

    def test_valid_ipv6(self):
        """测试有效IPv6地址"""
        valid_ips = [
            "::1",
            "fe80::1",
            "2001:db8::1",
            "2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        ]

        for ip in valid_ips:
            result = validate_ip(ip)
            assert result is not None, f"IPv6 {ip} 应该验证通过"

    def test_invalid_ips(self):
        """测试无效IP地址"""
        invalid_ips = [
            "",
            "   ",
            "256.256.256.256",
            "192.168.1",
            "192.168.1.1.1",
            "192.168.1.1:80",
            "192.168.1.1/24",
            "example.com",
        ]

        for ip in invalid_ips:
            with pytest.raises(ValidationException):
                validate_ip(ip)

    def test_private_ip_restriction(self):
        """测试私有IP限制"""
        # 应该允许私有IP（默认配置）
        result = validate_ip("192.168.1.1")
        assert result is not None


class TestValidateUrl:
    """URL验证测试"""

    def test_valid_urls(self):
        """测试有效URL"""
        valid_urls = [
            "http://example.com",
            "https://example.com",
            "http://example.com:8080",
            "https://sub.example.com/path",
            "http://192.168.1.1",
        ]

        for url in valid_urls:
            result = validate_url(url)
            assert result is not None, f"URL {url} 应该验证通过"

    def test_invalid_urls(self):
        """测试无效URL"""
        invalid_urls = [
            "",
            "   ",
            "example.com",  # 没有协议
            "ftp://example.com",  # 不支持FTP
            "file:///etc/passwd",  # 不支持file协议
            "javascript:alert(1)",  # XSS尝试
        ]

        for url in invalid_urls:
            with pytest.raises(ValidationException):
                validate_url(url)


class TestValidatePort:
    """端口验证测试"""

    def test_valid_ports(self):
        """测试有效端口"""
        valid_ports = [1, 80, 443, 8080, 8443, 65535]

        for port in valid_ports:
            result = validate_port(port)
            assert result is True, f"端口 {port} 应该验证通过"

    def test_invalid_ports(self):
        """测试无效端口"""
        invalid_ports = [-1, 0, 65536, 100000, "abc"]

        for port in invalid_ports:
            with pytest.raises(ValidationException):
                validate_port(port)


class TestSanitizeInput:
    """输入清理测试"""

    def test_basic_sanitization(self):
        """测试基本清理"""
        result = sanitize_input("plain text")
        assert result == "plain text"

    def test_html_escape(self):
        """测试HTML转义"""
        result = sanitize_input("<script>alert('xss')</script>")
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&amp;" in result or "&#x27;" in result

    def test_control_characters_removal(self):
        """测试控制字符移除"""
        result = sanitize_input("hello\x00world")
        assert "\x00" not in result

    def test_max_length_truncation(self):
        """测试最大长度截断"""
        long_input = "a" * 2000
        result = sanitize_input(long_input, max_length=1000)
        assert len(result) == 1000

    def test_empty_input(self):
        """测试空输入"""
        result = sanitize_input("")
        assert result == ""

    def test_whitespace_strip(self):
        """测试空白字符去除"""
        result = sanitize_input("  hello  ")
        assert result == "hello"


class TestValidateTaskType:
    """任务类型验证测试"""

    def test_valid_task_types(self):
        """测试有效任务类型"""
        valid_types = ["domain", "ip", "risk_cruising", "asset_site_update", "fofa", "asset_site_add", "asset_wih_update"]

        for task_type in valid_types:
            result = validate_task_type(task_type)
            assert result is True

    def test_invalid_task_type(self):
        """测试无效任务类型"""
        with pytest.raises(ValidationException):
            validate_task_type("invalid")

        with pytest.raises(ValidationException):
            validate_task_type("")

        with pytest.raises(ValidationException):
            validate_task_type("scan")
