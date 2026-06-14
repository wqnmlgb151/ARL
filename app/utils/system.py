# -*- coding: utf-8 -*-
"""
ARL 系统工具模块
提供进程管理、命令执行等系统级功能
"""

import os
import subprocess
import shlex
import random
import string
import logging
from typing import List, Any, Optional

import psutil

logger = logging.getLogger(__name__)


def exec_system(cmd: List[str], **kwargs: Any) -> subprocess.CompletedProcess:
    """
    执行系统命令

    Args:
        cmd: 命令列表
        **kwargs: 传递给 subprocess.run 的参数

    Returns:
        CompletedProcess 对象
    """
    cmd_str = " ".join(cmd)
    timeout = 4 * 60 * 60  # 4小时超时

    if kwargs.get('timeout'):
        timeout = kwargs['timeout']
        kwargs.pop('timeout')

    completed = subprocess.run(
        shlex.split(cmd_str),
        timeout=timeout,
        check=False,
        close_fds=True,
        **kwargs
    )

    return completed


def check_output(cmd: List[str], **kwargs: Any) -> bytes:
    """
    执行命令并返回输出

    Args:
        cmd: 命令列表
        **kwargs: 传递给 subprocess.run 的参数

    Returns:
        命令输出（bytes）
    """
    cmd_str = " ".join(cmd)
    timeout = 4 * 60 * 60

    if kwargs.get('timeout'):
        timeout = kwargs.pop('timeout')

    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')

    output = subprocess.run(
        shlex.split(cmd_str),
        stdout=subprocess.PIPE,
        timeout=timeout,
        check=False,
        **kwargs
    ).stdout
    return output


def random_choices(k: int = 6) -> str:
    """
    生成随机字符串

    Args:
        k: 字符串长度

    Returns:
        随机字符串
    """
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=k))


def kill_child_process(pid: int) -> None:
    """
    杀死子进程

    Args:
        pid: 父进程 PID
    """
    parent = psutil.Process(pid)
    for child in parent.children(recursive=True):
        logger.info(f"kill child_process {child}")
        child.kill()


def exit_gracefully(signum: int, frame: Any) -> None:
    """
    优雅退出进程

    Args:
        signum: 信号编号
        frame: 当前帧
    """
    logger.info(f'Receive signal {signum} frame {frame}')
    pid = os.getpid()
    kill_child_process(pid)
    parent = psutil.Process(pid)
    logger.info(f"kill self {parent}")
    parent.kill()


def is_valid_exclude_ports(exclude_ports: str) -> bool:
    """
    检查 nmap 排除端口范围是否合法

    Args:
        exclude_ports: 端口范围字符串（如 "80,443,8000-9000"）

    Returns:
        是否合法
    """
    port_pattern = r'(\d+(-\d+)?,?)+'
    match = re.fullmatch(port_pattern, exclude_ports)

    if not match:
        return False

    parts = exclude_ports.split(',')
    for part in parts:
        if '-' in part:
            start, end = map(int, part.split('-'))
            if start > end or not (0 <= start <= 65535) or not (0 <= end <= 65535):
                return False
        else:
            if not (0 <= int(part) <= 65535):
                return False

    return True


# 导入 re 模块（用于 is_valid_exclude_ports）
import re
