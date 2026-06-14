import secrets
import logging
from datetime import datetime, timedelta
from typing import Optional
from flask import request
from app import modules
from app.config import Config

logger = logging.getLogger(__name__)


def _get_conn_db():
    """延迟导入 conn_db 避免循环依赖"""
    from app.utils.db import conn_db
    return conn_db

# 密码哈希算法 - 只使用 bcrypt
import bcrypt


def hash_password(password: str) -> str:
    """
    哈希密码（仅使用 bcrypt）

    Args:
        password: 明文密码

    Returns:
        哈希后的密码
    """
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """
    验证密码（仅支持 bcrypt）

    Args:
        password: 明文密码
        hashed: 哈希后的密码

    Returns:
        是否匹配
    """
    try:
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
    except (ValueError, TypeError):
        # 无效的哈希格式
        return False


def generate_token() -> str:
    """生成安全的随机令牌"""
    return secrets.token_urlsafe(32)


def user_login(username=None, password=None):
    """
    用户登录

    Args:
        username: 用户名
        password: 密码

    Returns:
        用户信息字典，登录失败返回 None
    """
    if not username or not password:
        return None

    # 输入验证
    if not isinstance(username, str) or not isinstance(password, str):
        return None

    if len(username) > 50 or len(password) > 128:
        return None

    # 查询用户
    hashed_password = hash_password(password)
    query = {"username": username, "password": hashed_password}

    if _get_conn_db()('user').find_one(query):
        # 生成安全令牌
        token = generate_token()
        expires_at = datetime.utcnow() + timedelta(hours=24)

        item = {
            "username": username,
            "token": token,
            "type": "login",
            "expires_at": expires_at
        }
        _get_conn_db()('user').update_one(
            query,
            {"$set": {"token": token, "expires_at": expires_at}}
        )

        return item

    return None


def user_login_header():
    token = request.headers.get("Token") or request.args.get("token")

    if not Config.AUTH:
        return True

    item = {
        "username": "ARL-API",
        "token": Config.API_KEY,
        "type": "api"
    }


    if not token:
        return False

    if token == Config.API_KEY:
        return item


    data = _get_conn_db()('user').find_one({"token": token})
    if data:
        # 检查令牌是否过期
        expires_at = data.get("expires_at")
        if expires_at and datetime.utcnow() > expires_at:
            # 令牌已过期，清除并返回False
            _get_conn_db()('user').update_one(
                {"token": token},
                {"$set": {"token": None, "expires_at": None}}
            )
            return False

        item["username"] = data.get("username")
        item["token"] = token
        item["type"] = "login"
        return item

    return False



def user_logout(token):
    """用户登出"""
    if not token:
        return

    # 清除令牌（无论是否过期都执行）
    _get_conn_db()('user').update_one(
        {"token": token},
        {"$set": {"token": None, "expires_at": None}}
    )


def change_pass(token, old_password, new_password):
    """
    修改密码

    Args:
        token: 用户令牌
        old_password: 旧密码
        new_password: 新密码

    Returns:
        是否修改成功
    """
    # 输入验证
    if not token or not old_password or not new_password:
        return False

    # 验证新密码强度
    if not validate_password_strength(new_password):
        return False

    query = {
        "token": token,
        "password": hash_password(old_password)
    }
    data = _get_conn_db()('user').find_one(query)
    if data:
        # 检查令牌是否过期
        expires_at = data.get("expires_at")
        if expires_at and datetime.utcnow() > expires_at:
            # 令牌已过期
            return False

        _get_conn_db()('user').update_one(
            {"token": token},
            {"$set": {"password": hash_password(new_password)}}
        )
        return True
    return False


def validate_password_strength(password: str) -> bool:
    """
    验证密码强度

    要求：
    - 至少 8 个字符
    - 包含大写字母
    - 包含小写字母
    - 包含数字
    """
    if len(password) < 8:
        return False
    if not any(c.isupper() for c in password):
        return False
    if not any(c.islower() for c in password):
        return False
    if not any(c.isdigit() for c in password):
        return False
    return True


import functools


def auth(func):
    ret = {
        "message": "not login",
        "code": 401,
        "data": {}
    }

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if Config.AUTH and not user_login_header():
            return  ret

        return func(*args, **kwargs)

    return wrapper