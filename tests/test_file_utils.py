# -*- coding: utf-8 -*-
"""
文件工具模块单元测试
"""

import os
import tempfile
import pytest
from pathlib import Path

from app.utils.file_utils import (
    load_file, load_file_silent, save_file, append_file,
    read_file_content, write_file_content, file_exists,
    get_file_size, ensure_directory
)


class TestLoadFile:
    """测试 load_file 函数"""

    def test_load_existing_file(self, tmp_path):
        """测试读取存在的文件"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("line1\nline2\nline3\n", encoding="utf-8")

        result = load_file(test_file)
        assert result == ["line1\n", "line2\n", "line3\n"]

    def test_load_nonexistent_file(self):
        """测试读取不存在的文件"""
        with pytest.raises(FileNotFoundError):
            load_file("/nonexistent/file.txt")

    def test_load_file_with_str_path(self, tmp_path):
        """测试使用字符串路径"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content\n", encoding="utf-8")

        result = load_file(str(test_file))
        assert result == ["content\n"]


class TestLoadFileSilent:
    """测试 load_file_silent 函数"""

    def test_load_existing_file(self, tmp_path):
        """测试读取存在的文件"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content\n", encoding="utf-8")

        result = load_file_silent(test_file)
        assert result == ["content\n"]

    def test_load_nonexistent_file(self):
        """测试读取不存在的文件返回空列表"""
        result = load_file_silent("/nonexistent/file.txt")
        assert result == []


class TestSaveFile:
    """测试 save_file 函数"""

    def test_save_new_file(self, tmp_path):
        """测试保存新文件"""
        test_file = tmp_path / "new_file.txt"
        lines = ["line1\n", "line2\n", "line3\n"]

        save_file(test_file, lines)

        assert test_file.exists()
        assert test_file.read_text(encoding="utf-8") == "line1\nline2\nline3\n"

    def test_save_creates_directories(self, tmp_path):
        """测试自动创建目录"""
        test_file = tmp_path / "subdir1" / "subdir2" / "file.txt"
        lines = ["content\n"]

        save_file(test_file, lines)

        assert test_file.exists()


class TestAppendFile:
    """测试 append_file 函数"""

    def test_append_to_existing_file(self, tmp_path):
        """测试追加到已存在文件"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("line1\n", encoding="utf-8")

        append_file(test_file, ["line2\n", "line3\n"])

        content = test_file.read_text(encoding="utf-8")
        assert content == "line1\nline2\nline3\n"

    def test_append_creates_file(self, tmp_path):
        """测试文件不存在时创建"""
        test_file = tmp_path / "new_file.txt"

        append_file(test_file, ["content\n"])

        assert test_file.exists()


class TestReadFileContent:
    """测试 read_file_content 函数"""

    def test_read_content(self, tmp_path):
        """测试读取文件内容"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!", encoding="utf-8")

        result = read_file_content(test_file)
        assert result == "Hello, World!"

    def test_read_nonexistent_file(self):
        """测试读取不存在的文件"""
        with pytest.raises(FileNotFoundError):
            read_file_content("/nonexistent/file.txt")


class TestWriteFileContent:
    """测试 write_file_content 函数"""

    def test_write_content(self, tmp_path):
        """测试写入内容"""
        test_file = tmp_path / "test.txt"

        write_file_content(test_file, "Hello, World!")

        assert test_file.exists()
        assert test_file.read_text(encoding="utf-8") == "Hello, World!"


class TestFileExists:
    """测试 file_exists 函数"""

    def test_existing_file(self, tmp_path):
        """测试存在的文件"""
        test_file = tmp_path / "test.txt"
        test_file.write_text("content", encoding="utf-8")

        assert file_exists(test_file) is True

    def test_nonexistent_file(self):
        """测试不存在的文件"""
        assert file_exists("/nonexistent/file.txt") is False

    def test_directory(self, tmp_path):
        """测试目录（不是文件）"""
        assert file_exists(tmp_path) is False


class TestGetFileSize:
    """测试 get_file_size 函数"""

    def test_get_size(self, tmp_path):
        """测试获取文件大小"""
        test_file = tmp_path / "test.txt"
        content = "Hello, World!"
        test_file.write_text(content, encoding="utf-8")

        size = get_file_size(test_file)
        assert size == len(content.encode("utf-8"))

    def test_nonexistent_file(self):
        """测试不存在的文件"""
        size = get_file_size("/nonexistent/file.txt")
        assert size == 0


class TestEnsureDirectory:
    """测试 ensure_directory 函数"""

    def test_create_directory(self, tmp_path):
        """测试创建目录"""
        new_dir = tmp_path / "new_dir"

        result = ensure_directory(new_dir)

        assert new_dir.exists()
        assert new_dir.is_dir()
        assert result == new_dir

    def test_existing_directory(self, tmp_path):
        """测试已存在的目录"""
        result = ensure_directory(tmp_path)

        assert tmp_path.exists()
        assert result == tmp_path
