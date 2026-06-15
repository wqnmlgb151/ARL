# -*- coding: utf-8 -*-
"""
ARL 工具函数模块（轻量级入口）

本模块仅提供 re-export 功能，具体实现分布在：
- app/utils/db.py: 数据库访问
- app/utils/system.py: 系统工具
- app/utils/network.py: 网络工具
- app/utils/parsers.py: 解析工具（域名、URL、证书等）

推荐用法：
    # 数据库访问
    from app.utils.db import conn_db, init_db

    # 系统工具
    from app.utils.system import exec_system, check_output

    # 网络工具
    from app.utils.network import domain_parsed, get_ip, get_fld

    # 解析工具
    from app.utils.parsers import parse_domain, parse_url
"""

# ============================================================================
# 数据库访问（从 db.py re-export）
# ============================================================================
from app.utils.db import conn_db, get_db, init_db

# ============================================================================
# 系统工具（从 system.py re-export）
# ============================================================================
from app.utils.system import (
    exec_system,
    check_output,
    kill_child_process,
    exit_gracefully,
    is_valid_exclude_ports,
    random_choices,
)

# ============================================================================
# 网络工具（从 network.py re-export）
# ============================================================================
from app.utils.network import (
    domain_parsed,
    get_ip,
    get_fld,
    gen_filename,
)

# ============================================================================
# 解析工具（从 parsers.py re-export）
# ============================================================================
from app.utils.parsers import (
    build_ret,
    get_domain,
    get_ip_from_domain,
)

# ============================================================================
# 字符串工具（从 string_utils.py re-export）
# ============================================================================
from app.utils.string_utils import truncate_string, gen_md5

# ============================================================================
# 文件工具（从 file_utils.py re-export）
# ============================================================================
from app.utils.file_utils import (
    load_file,
    save_file,
    append_file,
    read_file_content,
    write_file_content,
)

# ============================================================================
# 路径常量（从 path_utils.py re-export）
# ============================================================================
from app.utils.path_utils import (
    BASE_DIR,
    DICTS_DIR,
    TOOLS_DIR,
    TMP_DIR,
    SCREENSHOT_DIR,
)

# ============================================================================
# 类型定义（从 type_defs.py re-export）
# ============================================================================
from app.utils.type_defs import (
    IPAddress,
    DomainName,
    PortNumber,
    URL,
    TaskStatus,
    SchedulerStatus,
    TaskType,
    AssetScopeType,
)

# ============================================================================
# 日志工具
# ============================================================================
import logging
import sys

try:
    from celery.utils.log import get_task_logger
except ImportError:
    def get_task_logger(name):
        return logging.getLogger(name)

import colorlog


def init_logger():
    """初始化日志记录器"""
    handler = colorlog.StreamHandler()
    handler.setFormatter(colorlog.ColoredFormatter(
        fmt='%(log_color)s[%(asctime)s] [%(levelname)s] '
             '[%(threadName)s] [%(filename)s:%(lineno)d] %(message)s',
        datefmt="%Y-%m-%d %H:%M:%S"
    ))

    logger = colorlog.getLogger('arlv2')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False


def get_logger():
    """获取日志记录器"""
    if 'celery' in sys.argv[0]:
        return get_task_logger(__name__)

    logger = logging.getLogger('arlv2')
    if not logger.handlers:
        init_logger()

    return logging.getLogger('arlv2')


# ============================================================================
# 向后兼容导入（将在后续版本中移除）
# ============================================================================
import os
import subprocess
import shlex
import hashlib
import re
from typing import List, Dict, Any, Optional, Tuple, Union

# 这些导入保留用于向后兼容，新代码应直接导入具体模块
from app.utils.sanitizer import MongoSanitizer, sanitize_input
from app.utils.user import verify_password, hash_password, auth
from app.utils.domain import is_valid_domain, check_domain_black
from app.utils.url import normal_url, get_hostname
from app.utils.http import get_title


# 延迟导入 http_req 避免循环依赖
def __getattr__(name):
    if name in ('http_req', 'http_client'):
        from app.utils.conn import http_req, http_client
        if name == 'http_req':
            return http_req
        return http_client
    raise AttributeError(f"module 'app.utils' has no attribute {name}")

# Windows 编码修复已移至 app/main.py（开发服务器入口）
