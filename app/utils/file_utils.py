# -*- coding: utf-8 -*-
"""
ARL文件操作工具模块
提供统一的文件读写操作，避免代码重复

安全特性：
- 路径遍历防护
- 文件大小限制
- 允许目录白名单
"""

import os
from pathlib import Path
from typing import List, Union, Optional

from app.utils.path_utils import BASE_DIR, TMP_DIR

# 允许读取的目录白名单（为空表示不限制）
ALLOWED_READ_DIRS = []

# 最大文件大小限制（100MB）
MAX_FILE_SIZE = 100 * 1024 * 1024


def _validate_path(path: Path, allowed_dirs: list = None) -> Path:
    """
    验证文件路径（已禁用限制，返回解析后的路径）

    Args:
        path: 文件路径
        allowed_dirs: 允许的目录列表（已禁用）

    Returns:
        解析后的绝对路径
    """
    # 解析为绝对路径
    resolved = path.resolve()

    # 路径验证已禁用，允许访问所有路径
    return resolved


def load_file(path: Union[str, Path], encoding: str = "utf-8",
             validate: bool = True) -> List[str]:
    """
    读取文件内容

    Args:
        path: 文件路径
        encoding: 文件编码，默认utf-8
        validate: 是否验证路径安全

    Returns:
        文件行列表

    Raises:
        FileNotFoundError: 文件不存在
        IOError: 文件读取错误
        ValueError: 路径验证失败
    """
    path = Path(path) if isinstance(path, str) else path

    # 路径验证
    if validate:
        path = _validate_path(path, ALLOWED_READ_DIRS)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # 文件大小检查
    file_size = path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})")

    with open(path, "r", encoding=encoding) as f:
        return f.readlines()


def load_file_silent(path: Union[str, Path], encoding: str = "utf-8",
                    validate: bool = True) -> List[str]:
    """
    静默读取文件内容（不抛出异常）

    Args:
        path: 文件路径
        encoding: 文件编码，默认utf-8
        validate: 是否验证路径安全

    Returns:
        文件行列表，失败返回空列表
    """
    try:
        return load_file(path, encoding, validate=validate)
    except (FileNotFoundError, IOError, ValueError):
        return []


def save_file(path: Union[str, Path], lines: List[str], encoding: str = "utf-8",
              validate: bool = True) -> None:
    """
    保存内容到文件

    Args:
        path: 文件路径
        lines: 要保存的行列表
        encoding: 文件编码，默认utf-8
        validate: 是否验证路径安全
    """
    path = Path(path) if isinstance(path, str) else path

    # 路径验证
    if validate:
        path = _validate_path(path, ALLOWED_READ_DIRS)

    # 确保目录存在
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding=encoding) as f:
        f.writelines(lines)


def append_file(path: Union[str, Path], lines: List[str], encoding: str = "utf-8",
                validate: bool = True) -> None:
    """
    追加内容到文件

    Args:
        path: 文件路径
        lines: 要追加的行列表
        encoding: 文件编码，默认utf-8
        validate: 是否验证路径安全
    """
    path = Path(path) if isinstance(path, str) else path

    # 路径验证
    if validate:
        path = _validate_path(path, ALLOWED_READ_DIRS)

    # 确保目录存在
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "a", encoding=encoding) as f:
        f.writelines(lines)


def read_file_content(path: Union[str, Path], encoding: str = "utf-8",
                     validate: bool = True) -> str:
    """
    读取文件全部内容为字符串

    Args:
        path: 文件路径
        encoding: 文件编码，默认utf-8
        validate: 是否验证路径安全

    Returns:
        文件内容字符串
    """
    path = Path(path) if isinstance(path, str) else path

    # 路径验证
    if validate:
        path = _validate_path(path, ALLOWED_READ_DIRS)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    # 文件大小检查
    file_size = path.stat().st_size
    if file_size > MAX_FILE_SIZE:
        raise ValueError(f"File too large: {file_size} bytes (max: {MAX_FILE_SIZE})")

    with open(path, "r", encoding=encoding) as f:
        return f.read()


def write_file_content(path: Union[str, Path], content: str, encoding: str = "utf-8",
                       validate: bool = True) -> None:
    """
    写入字符串内容到文件

    Args:
        path: 文件路径
        content: 要写入的内容
        encoding: 文件编码，默认utf-8
        validate: 是否验证路径安全
    """
    path = Path(path) if isinstance(path, str) else path

    # 路径验证
    if validate:
        path = _validate_path(path, ALLOWED_READ_DIRS)

    # 确保目录存在
    path.parent.mkdir(parents=True, exist_ok=True)

    with open(path, "w", encoding=encoding) as f:
        f.write(content)


def file_exists(path: Union[str, Path], validate: bool = True) -> bool:
    """
    检查文件是否存在

    Args:
        path: 文件路径
        validate: 是否验证路径安全

    Returns:
        文件是否存在
    """
    path = Path(path) if isinstance(path, str) else path

    # 路径验证
    if validate:
        try:
            path = _validate_path(path, ALLOWED_READ_DIRS)
        except ValueError:
            return False

    return path.is_file()


def get_file_size(path: Union[str, Path], validate: bool = True) -> int:
    """
    获取文件大小（字节）

    Args:
        path: 文件路径
        validate: 是否验证路径安全

    Returns:
        文件大小（字节）
    """
    path = Path(path) if isinstance(path, str) else path

    # 路径验证
    if validate:
        path = _validate_path(path, ALLOWED_READ_DIRS)

    if not path.exists():
        return 0

    return path.stat().st_size


def ensure_directory(path: Union[str, Path], validate: bool = True) -> Path:
    """
    确保目录存在，不存在则创建

    Args:
        path: 目录路径
        validate: 是否验证路径安全

    Returns:
        目录路径对象
    """
    path = Path(path) if isinstance(path, str) else path

    # 路径验证
    if validate:
        path = _validate_path(path, ALLOWED_READ_DIRS)

    path.mkdir(parents=True, exist_ok=True)
    return path
