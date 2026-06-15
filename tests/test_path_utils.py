# -*- coding: utf-8 -*-
"""
路径工具模块单元测试
"""

import pytest
from pathlib import Path

from app.utils.path_utils import (
    BASE_DIR, DICTS_DIR, TOOLS_DIR, TMP_DIR, SCREENSHOT_DIR,
    DICT_FILES, TOOL_FILES, DNS_QUERY_PLUGIN_DIR,
    get_dict_path, get_tool_path, ensure_directories,
    is_valid_path, is_dict_file, get_file_name, get_file_suffix,
    join_path, normalize_path
)


class TestPathConstants:
    """测试路径常量"""

    def test_base_dir_exists(self):
        """测试BASE_DIR存在"""
        assert BASE_DIR.exists()
        assert BASE_DIR.is_dir()

    def test_dicts_dir(self):
        """测试DICTS_DIR"""
        assert DICTS_DIR == BASE_DIR / 'dicts'

    def test_tools_dir(self):
        """测试TOOLS_DIR"""
        assert TOOLS_DIR == BASE_DIR / 'tools'

    def test_tmp_dir(self):
        """测试TMP_DIR"""
        assert TMP_DIR == BASE_DIR / 'tmp'

    def test_screenshot_dir(self):
        """测试SCREENSHOT_DIR"""
        assert SCREENSHOT_DIR == BASE_DIR / 'tmp_screenshot'


class TestDictFiles:
    """测试字典文件路径"""

    def test_domain_test_key(self):
        """测试domain_test键"""
        assert 'domain_test' in DICT_FILES
        assert DICT_FILES['domain_test'] == DICTS_DIR / 'domain_dict_test.txt'

    def test_domain_2w_key(self):
        """测试domain_2w键"""
        assert 'domain_2w' in DICT_FILES
        assert DICT_FILES['domain_2w'] == DICTS_DIR / 'domain_2w.txt'


class TestToolFiles:
    """测试工具文件路径"""

    def test_massdns_key(self):
        """测试massdns键"""
        assert 'massdns' in TOOL_FILES
        assert TOOL_FILES['massdns'] == TOOLS_DIR / 'massdns'

    def test_screenshot_js_key(self):
        """测试screenshot_js键"""
        assert 'screenshot_js' in TOOL_FILES
        assert TOOL_FILES['screenshot_js'] == TOOLS_DIR / 'screenshot.js'


class TestGetDictPath:
    """测试 get_dict_path 函数"""

    def test_valid_dict(self):
        """测试有效字典名称"""
        path = get_dict_path('domain_test')
        assert path == DICTS_DIR / 'domain_dict_test.txt'

    def test_invalid_dict(self):
        """测试无效字典名称"""
        path = get_dict_path('nonexistent')
        assert path is None


class TestGetToolPath:
    """测试 get_tool_path 函数"""

    def test_valid_tool(self):
        """测试有效工具名称"""
        path = get_tool_path('massdns')
        assert path == TOOLS_DIR / 'massdns'

    def test_invalid_tool(self):
        """测试无效工具名称"""
        path = get_tool_path('nonexistent')
        assert path is None


class TestEnsureDirectories:
    """测试 ensure_directories 函数"""

    def test_creates_directories(self, tmp_path):
        """测试创建目录"""
        # 临时修改全局常量
        import app.utils.path_utils as path_utils
        original_tmp = path_utils.TMP_DIR
        original_screenshot = path_utils.SCREENSHOT_DIR

        try:
            path_utils.TMP_DIR = tmp_path / 'tmp'
            path_utils.SCREENSHOT_DIR = tmp_path / 'screenshot'

            ensure_directories()

            assert (tmp_path / 'tmp').exists()
            assert (tmp_path / 'screenshot').exists()
        finally:
            path_utils.TMP_DIR = original_tmp
            path_utils.SCREENSHOT_DIR = original_screenshot


class TestIsValidPath:
    """测试 is_valid_path 函数"""

    def test_valid_path(self, tmp_path):
        """测试有效路径"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content", encoding="utf-8")

        assert is_valid_path(test_file) is True

    def test_invalid_path(self):
        """测试无效路径"""
        assert is_valid_path(Path("/nonexistent/path")) is False


class TestIsDictFile:
    """测试 is_dict_file 函数"""

    def test_txt_file(self, tmp_path):
        """测试txt文件"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content", encoding="utf-8")

        assert is_dict_file(test_file) is True

    def test_json_file(self, tmp_path):
        """测试json文件"""
        test_file = tmp_path / "test.json"
        test_file.write_text("{}", encoding="utf-8")

        assert is_dict_file(test_file) is True

    def test_yml_file(self, tmp_path):
        """测试yml文件"""
        test_file = tmp_path / "test.yml"
        test_file.write_text("key: value", encoding="utf-8")

        assert is_dict_file(test_file) is True

    def test_yaml_file(self, tmp_path):
        """测试yaml文件"""
        test_file = tmp_path / "test.yaml"
        test_file.write_text("key: value", encoding="utf-8")

        assert is_dict_file(test_file) is True

    def test_py_file(self, tmp_path):
        """测试py文件（不是字典文件）"""
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')", encoding="utf-8")

        assert is_dict_file(test_file) is False


class TestGetFileName:
    """测试 get_file_name 函数"""

    def test_get_name(self):
        """测试获取文件名"""
        path = Path("/home/user/test.txt")
        assert get_file_name(path) == "test.txt"

    def test_get_name_no_path(self):
        """测试只有文件名"""
        path = Path("test.txt")
        assert get_file_name(path) == "test.txt"


class TestGetFileSuffix:
    """测试 get_file_suffix 函数"""

    def test_get_suffix(self):
        """测试获取扩展名"""
        path = Path("/home/user/test.txt")
        assert get_file_suffix(path) == ".txt"

    def test_no_suffix(self):
        """测试无扩展名"""
        path = Path("/home/user/test")
        assert get_file_suffix(path) == ""


class TestJoinPath:
    """测试 join_path 函数"""

    def test_join_paths(self):
        """测试连接路径"""
        result = join_path("/home", "user", "test.txt")
        assert result == Path("/home/user/test.txt")


class TestNormalizePath:
    """测试 normalize_path 函数"""

    def test_normalize_path(self):
        """测试规范化路径"""
        path = Path("/home/user/../user/./test.txt")
        result = normalize_path(path)
        assert result == Path("/home/user/test.txt")
