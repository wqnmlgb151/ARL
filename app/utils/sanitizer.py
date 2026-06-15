# -*- coding: utf-8 -*-
"""
MongoDB 输入清理工具
防止 NoSQL 注入攻击
"""

import re
from typing import Any, Dict, List, Optional, Union
from bson import ObjectId
from bson.errors import InvalidId


class MongoSanitizer:
    """MongoDB 查询清理器"""
    
    # 危险的 MongoDB 操作符
    DANGEROUS_OPERATORS = {
        '$gt', '$gte', '$lt', '$lte', '$ne', '$nin', '$in',
        '$regex', '$exists', '$type', '$mod', '$text', '$where',
        '$or', '$and', '$not', '$nor', '$expr', '$jsonSchema',
        '$all', '$elemMatch', '$size', '$bitsAllSet', '$bitsAnySet'
    }
    
    @staticmethod
    def sanitize_string(value: str) -> str:
        """清理字符串值，移除 MongoDB 操作符"""
        if not isinstance(value, str):
            return str(value)
        
        # 移除 null 字节
        value = value.replace('\x00', '')
        
        # 限制长度防止 DoS
        if len(value) > 1000:
            value = value[:1000]
        
        return value
    
    @staticmethod
    def sanitize_objectid(value: str) -> Optional[ObjectId]:
        """安全转换 ObjectId"""
        if not isinstance(value, str):
            return None
        
        # ObjectId 必须是 24 位十六进制字符串
        if not re.match(r'^[0-9a-fA-F]{24}$', value):
            return None
        
        try:
            return ObjectId(value)
        except (InvalidId, TypeError):
            return None
    
    @classmethod
    def sanitize_query(cls, query: Dict[str, Any]) -> Dict[str, Any]:
        """清理 MongoDB 查询字典"""
        if not isinstance(query, dict):
            return {}
        
        cleaned = {}
        for key, value in query.items():
            # 跳过危险操作符
            if key.startswith('$') and key in cls.DANGEROUS_OPERATORS:
                continue
            
            # 清理键名
            clean_key = cls.sanitize_string(key) if isinstance(key, str) else key
            
            # 递归清理值
            clean_value = cls.sanitize_value(value)
            cleaned[clean_key] = clean_value
        
        return cleaned
    
    @classmethod
    def sanitize_value(cls, value: Any) -> Any:
        """递归清理值"""
        if isinstance(value, dict):
            return cls.sanitize_query(value)
        elif isinstance(value, list):
            return [cls.sanitize_value(item) for item in value]
        elif isinstance(value, str):
            return cls.sanitize_string(value)
        else:
            return value
    
    @staticmethod
    def safe_find_one(collection, query: Dict[str, Any]) -> Optional[Dict]:
        """安全的 find_one 查询"""
        cleaned_query = MongoSanitizer.sanitize_query(query)
        return collection.find_one(cleaned_query)
    
    @staticmethod
    def safe_find(collection, query: Dict[str, Any]) -> List[Dict]:
        """安全的 find 查询"""
        cleaned_query = MongoSanitizer.sanitize_query(query)
        return list(collection.find(cleaned_query))
    
    @staticmethod
    def safe_insert_one(collection, document: Dict[str, Any]) -> bool:
        """安全的 insert_one 操作"""
        cleaned_doc = MongoSanitizer.sanitize_value(document)
        try:
            collection.insert_one(cleaned_doc)
            return True
        except Exception:
            return False
    
    @staticmethod
    def safe_update_one(collection, filter_query: Dict, update: Dict) -> bool:
        """安全的 update_one 操作"""
        cleaned_filter = MongoSanitizer.sanitize_query(filter_query)
        cleaned_update = MongoSanitizer.sanitize_value(update)
        try:
            collection.update_one(cleaned_filter, cleaned_update)
            return True
        except Exception:
            return False
    
    @staticmethod
    def safe_delete_one(collection, query: Dict[str, Any]) -> bool:
        """安全的 delete_one 操作"""
        cleaned_query = MongoSanitizer.sanitize_query(query)
        try:
            collection.delete_one(cleaned_query)
            return True
        except Exception:
            return False


def sanitize_input(value: Any, field_type: str = 'string') -> Any:
    """
    清理用户输入的便捷函数
    
    Args:
        value: 用户输入值
        field_type: 字段类型 ('string', 'objectid', 'int', 'bool')
    
    Returns:
        清理后的值
    """
    if field_type == 'objectid':
        return MongoSanitizer.sanitize_objectid(str(value))
    elif field_type == 'int':
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0
    elif field_type == 'bool':
        return bool(value)
    else:
        return MongoSanitizer.sanitize_string(str(value))


def validate_object_id(id_str: str) -> bool:
    """验证 ObjectId 格式"""
    if not isinstance(id_str, str):
        return False
    return bool(re.match(r'^[0-9a-fA-F]{24}$', id_str))
