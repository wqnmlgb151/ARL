# -*- coding: utf-8 -*-
"""
ARL单元测试包
"""
import importlib

__all__ = [
    "test_validators",
    "test_exceptions",
    "test_permissions",
    "test_types",
    "test_services",
    "test_repositories",
    "test_audit",
    "test_database",
    "test_export",
]

_modules = {}


def __getattr__(name):
    """延迟导入测试模块"""
    if name in __all__:
        if name not in _modules:
            try:
                _modules[name] = importlib.import_module(f".{name}", package=__name__)
            except ImportError as e:
                import warnings
                warnings.warn(f"Could not import {name}: {e}")
                return None
        return _modules[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
