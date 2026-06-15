# -*- coding: utf-8 -*-
"""
ARL数据库模块
提供统一的数据库访问接口
"""

from app.database.connection import DatabaseManager, get_collection, get_db, init_db
from app.database.repositories import BaseRepository

__all__ = ['DatabaseManager', 'get_collection', 'get_db', 'init_db', 'BaseRepository']
