# -*- coding: utf-8 -*-
"""
ARL用户服务
封装用户认证和管理的业务逻辑
"""

import secrets
import logging
from datetime import datetime
from typing import Dict, Optional, Tuple

import bcrypt

from app.core.exceptions import AuthenticationException, ValidationException, NotFoundException
from app.core.audit import audit_log
from app.database.repositories import UserRepository
from app.core.types import UserInfo

logger = logging.getLogger(__name__)


class UserService:
    """
    用户服务

    封装用户认证和管理的业务逻辑，包括：
    - 用户登录/登出
    - 密码管理
    - API Key管理
    - Token验证

    用法：
        service = UserService()
        user, token = service.authenticate('admin', 'password')
    """

    def __init__(self):
        self.repo = UserRepository()

    def _hash_password(self, password: str) -> str:
        """
        密码哈希（使用bcrypt）

        Args:
            password: 明文密码

        Returns:
            哈希后的密码
        """
        # bcrypt automatically handles salt generation
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def _verify_password(self, password: str, password_hash: str) -> bool:
        """
        验证密码（仅支持 bcrypt）

        Args:
            password: 明文密码
            password_hash: 哈希后的密码

        Returns:
            密码是否匹配
        """
        try:
            return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        except (ValueError, TypeError):
            # 无效的哈希格式（包括旧版 MD5）
            return False

    def _generate_token(self) -> str:
        """生成随机Token"""
        return secrets.token_urlsafe(32)

    def _generate_api_key(self) -> str:
        """生成API Key"""
        return f"arl_{secrets.token_urlsafe(24)}"

    @audit_log(action='login', resource='user')
    def authenticate(self, username: str, password: str) -> Tuple[Dict, str]:
        """
        用户认证

        Args:
            username: 用户名
            password: 密码

        Returns:
            (用户信息, Token)元组

        Raises:
            AuthenticationException: 认证失败
        """
        # 验证输入
        if not username or not password:
            raise AuthenticationException("Username and password are required")

        # 查找用户
        user = self.repo.find_by_username(username)
        if not user:
            logger.warning(f"Login failed: user not found - {username}")
            raise AuthenticationException("Invalid username or password")

        # 检查用户状态
        if not user.get('is_active', True):
            logger.warning(f"Login failed: user inactive - {username}")
            raise AuthenticationException("User account is disabled")

        # 验证密码
        if not self._verify_password(password, user['password_hash']):
            logger.warning(f"Login failed: wrong password - {username}")
            raise AuthenticationException("Invalid username or password")

        # 生成Token
        token = self._generate_token()

        # 更新Token和最后登录时间
        self.repo.update_one(
            {'username': username},
            {
                '$set': {
                    'token': token,
                    'last_login': datetime.now()
                }
            }
        )

        logger.info(f"User authenticated: {username}")

        # 返回用户信息（不包含密码）
        user_info = {
            'username': user['username'],
            'role': user.get('role', 'viewer'),
            'api_key': user.get('api_key')
        }

        return user_info, token

    def verify_token(self, token: str) -> Optional[Dict]:
        """
        验证Token

        Args:
            token: 用户Token

        Returns:
            用户信息，验证失败返回None
        """
        if not token:
            return None

        user = self.repo.find_by_token(token)
        if not user:
            return None

        return {
            'username': user['username'],
            'role': user.get('role', 'viewer')
        }

    def verify_api_key(self, api_key: str) -> Optional[Dict]:
        """
        验证API Key

        Args:
            api_key: API Key

        Returns:
            用户信息，验证失败返回None
        """
        if not api_key:
            return None

        user = self.repo.find_by_api_key(api_key)
        if not user:
            return None

        return {
            'username': user['username'],
            'role': user.get('role', 'viewer')
        }

    def change_password(
        self,
        username: str,
        old_password: str,
        new_password: str
    ) -> bool:
        """
        修改密码

        Args:
            username: 用户名
            old_password: 旧密码
            new_password: 新密码

        Returns:
            是否修改成功

        Raises:
            AuthenticationException: 旧密码错误
            ValidationException: 新密码不符合要求
        """
        # 验证新密码强度
        if len(new_password) < 6:
            raise ValidationException("Password must be at least 6 characters", field='new_password')

        # 查找用户
        user = self.repo.find_by_username(username)
        if not user:
            raise NotFoundException(f"User not found: {username}", resource_type='user')

        # 验证旧密码
        if not self._verify_password(old_password, user['password_hash']):
            raise AuthenticationException("Current password is incorrect")

        # 更新密码
        new_hash = self._hash_password(new_password)
        success = self.repo.update_one(
            {'username': username},
            {
                '$set': {
                    'password_hash': new_hash,
                    'updated_at': datetime.now()
                }
            }
        )

        if success:
            logger.info(f"Password changed for user: {username}")

        return success

    def reset_api_key(self, username: str) -> str:
        """
        重置API Key

        Args:
            username: 用户名

        Returns:
            新的API Key

        Raises:
            NotFoundException: 用户不存在
        """
        user = self.repo.find_by_username(username)
        if not user:
            raise NotFoundException(f"User not found: {username}", resource_type='user')

        new_api_key = self._generate_api_key()
        self.repo.update_one(
            {'username': username},
            {
                '$set': {
                    'api_key': new_api_key,
                    'updated_at': datetime.now()
                }
            }
        )

        logger.info(f"API key reset for user: {username}")
        return new_api_key

    def create_user(
        self,
        username: str,
        password: str,
        role: str = 'viewer',
        created_by: Optional[str] = None
    ) -> Dict:
        """
        创建用户

        Args:
            username: 用户名
            password: 密码
            role: 角色
            created_by: 创建者

        Returns:
            用户信息

        Raises:
            ValidationException: 用户名已存在或参数无效
        """
        # 验证用户名
        if not username or len(username) < 3:
            raise ValidationException("Username must be at least 3 characters", field='username')

        # 验证密码强度
        if len(password) < 6:
            raise ValidationException("Password must be at least 6 characters", field='password')

        # 检查用户名是否已存在
        existing_user = self.repo.find_by_username(username)
        if existing_user:
            raise ValidationException(f"Username already exists: {username}", field='username')

        # 生成密码哈希和API Key
        password_hash = self._hash_password(password)
        api_key = self._generate_api_key()

        # 创建用户文档
        user_doc = {
            'username': username,
            'password_hash': password_hash,
            'role': role,
            'api_key': api_key,
            'is_active': True,
            'created_at': datetime.now(),
            'created_by': created_by
        }

        user_id = self.repo.insert_one(user_doc)

        logger.info(f"User created: {username} with role {role}")

        return {
            'id': user_id,
            'username': username,
            'role': role,
            'api_key': api_key
        }

    def deactivate_user(self, username: str) -> bool:
        """
        停用用户

        Args:
            username: 用户名

        Returns:
            是否停用成功
        """
        user = self.repo.find_by_username(username)
        if not user:
            raise NotFoundException(f"User not found: {username}", resource_type='user')

        success = self.repo.deactivate_user(username)

        if success:
            logger.info(f"User deactivated: {username}")

        return success

    def get_user_info(self, username: str) -> Dict:
        """
        获取用户信息

        Args:
            username: 用户名

        Returns:
            用户信息（不包含密码）

        Raises:
            NotFoundException: 用户不存在
        """
        user = self.repo.find_by_username(username)
        if not user:
            raise NotFoundException(f"User not found: {username}", resource_type='user')

        return {
            'username': user['username'],
            'role': user.get('role', 'viewer'),
            'api_key': user.get('api_key'),
            'is_active': user.get('is_active', True),
            'last_login': user.get('last_login'),
            'created_at': user.get('created_at')
        }

    def list_users(self, active_only: bool = True) -> list:
        """
        查询用户列表

        Args:
            active_only: 是否只返回活跃用户

        Returns:
            用户列表
        """
        if active_only:
            return self.repo.find_active_users()
        return self.repo.find_many({})
