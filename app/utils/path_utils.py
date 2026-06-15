# -*- coding: utf-8 -*-
"""
ARL路径处理工具模块
提供统一的路径常量和管理函数，避免路径构建重复
"""

from pathlib import Path
from typing import Optional


# 项目根目录（app目录）
BASE_DIR = Path(__file__).parent.parent.resolve()

# 字典文件目录
DICTS_DIR = BASE_DIR / 'dicts'

# 工具文件目录
TOOLS_DIR = BASE_DIR / 'tools'

# 临时文件目录
TMP_DIR = BASE_DIR / 'tmp'

# 截图目录
SCREENSHOT_DIR = BASE_DIR / 'tmp_screenshot'

# 服务目录
SERVICES_DIR = BASE_DIR / 'services'

# 路由目录
ROUTES_DIR = BASE_DIR / 'routes'

# 任务目录
TASKS_DIR = BASE_DIR / 'tasks'

# 辅助目录
HELPERS_DIR = BASE_DIR / 'helpers'

# 模块目录
MODULES_DIR = BASE_DIR / 'modules'

# 字典文件路径
DICT_FILES = {
    'domain_test': DICTS_DIR / 'domain_dict_test.txt',
    'domain_2w': DICTS_DIR / 'domain_2w.txt',
    'dns_server': DICTS_DIR / 'dnsserver.txt',
    'cdn_json': DICTS_DIR / 'cdn_info.json',
    'wih_rules': DICTS_DIR / 'wih_rules.yml',
    'black_domain': DICTS_DIR / 'blackdomain.txt',
    'black_hexie': DICTS_DIR / 'blackhexie.txt',
    'black_asset_site': DICTS_DIR / 'black_asset_site.txt',
    'alt_dns_dict': DICTS_DIR / 'altdnsdict.txt',
    'web_app': DICTS_DIR / 'webapp.json',
    'file_leak_2k': DICTS_DIR / 'file_top_2000.txt',
    'file_leak_200': DICTS_DIR / 'file_top_200.txt',
}

# 工具文件路径
TOOL_FILES = {
    'massdns': TOOLS_DIR / 'massdns',
    'screenshot_js': TOOLS_DIR / 'screenshot.js',
    'driver_js': TOOLS_DIR / 'driver.js',
    'noscreenshot': DICTS_DIR / 'noscreenshot.jpg',
}

# DNS查询插件目录
DNS_QUERY_PLUGIN_DIR = SERVICES_DIR / 'dns_query_plugin'


def get_dict_path(dict_name: str) -> Optional[Path]:
    """
    获取字典文件路径

    Args:
        dict_name: 字典名称（使用DICT_FILES的键名）

    Returns:
        字典文件路径，不存在返回None
    """
    return DICT_FILES.get(dict_name)


def get_tool_path(tool_name: str) -> Optional[Path]:
    """
    获取工具文件路径

    Args:
        tool_name: 工具名称（使用TOOL_FILES的键名）

    Returns:
        工具文件路径，不存在返回None
    """
    return TOOL_FILES.get(tool_name)


def ensure_directories() -> None:
    """
    确保必要的目录存在
    """
    directories = [
        TMP_DIR,
        SCREENSHOT_DIR,
        DICTS_DIR,
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def is_valid_path(path: Path) -> bool:
    """
    检查路径是否存在

    Args:
        path: 路径对象

    Returns:
        是否存在
    """
    return path.exists()


def is_dict_file(path: Path) -> bool:
    """
    检查路径是否为字典文件（存在且是文件）

    Args:
        path: 路径对象

    Returns:
        是否为字典文件
    """
    return path.is_file() and path.suffix in ['.txt', '.json', '.yml', '.yaml']


def get_file_name(path: Path) -> str:
    """
    获取文件名（不含路径）

    Args:
        path: 路径对象

    Returns:
        文件名
    """
    return path.name


def get_file_suffix(path: Path) -> str:
    """
    获取文件扩展名

    Args:
        path: 路径对象

    Returns:
        文件扩展名（包含点）
    """
    return path.suffix


def join_path(*parts) -> Path:
    """
    连接路径

    Args:
        *parts: 路径部分

    Returns:
        连接后的路径
    """
    return Path(*parts)


def normalize_path(path: Path) -> Path:
    """
    规范化路径（解析..和.）

    Args:
        path: 路径对象

    Returns:
        规范化后的路径
    """
    return path.resolve()
