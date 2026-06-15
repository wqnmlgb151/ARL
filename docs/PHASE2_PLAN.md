# 第二阶段：架构优化实施计划

## 概述

第二阶段将重点进行架构优化，包括 Redis 缓存层引入、插件系统基础框架搭建，以及服务拆分的前期准备工作。

**预计时间**: 3-4周
**开始日期**: 2026-06-12

---

## 任务分解

### 2.1 Redis 缓存层引入（第1周）

#### 任务 2.1.1: Redis 基础设施搭建
**目标**: 引入 Redis 作为缓存层

**具体工作**:
- [ ] 安装 Redis（本地开发环境）
- [ ] 创建 Redis 连接管理模块 `app/utils/redis_utils.py`
- [ ] 实现缓存装饰器 `@cache_result`
- [ ] 添加缓存配置到 `app/config.py`

**技术要点**:
```python
# app/utils/redis_utils.py
import redis
from functools import wraps
from typing import Optional, Callable, Any

class RedisManager:
    def __init__(self):
        self.client: Optional[redis.Redis] = None

    def init_app(self, app_config: dict) -> None:
        """初始化Redis连接"""
        self.client = redis.Redis(
            host=app_config.get('REDIS_HOST', 'localhost'),
            port=app_config.get('REDIS_PORT', 6379),
            db=app_config.get('REDIS_DB', 0),
            decode_responses=True
        )

    def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        return self.client.get(key) if self.client else None

    def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """设置缓存值"""
        if self.client:
            return self.client.setex(key, ttl, value)
        return False

    def delete(self, key: str) -> bool:
        """删除缓存值"""
        if self.client:
            return self.client.delete(key) > 0
        return False

redis_manager = RedisManager()


def cache_result(ttl: int = 3600, key_prefix: str = ""):
    """缓存装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # 尝试从缓存获取
            cached = redis_manager.get(cache_key)
            if cached:
                import json
                return json.loads(cached)

            # 执行函数
            result = func(*args, **kwargs)

            # 存入缓存
            import json
            redis_manager.set(cache_key, json.dumps(result, default=str), ttl)

            return result
        return wrapper
    return decorator
```

#### 任务 2.1.2: 实现缓存策略
**目标**: 为高频查询添加缓存

**缓存项**:
- DNS 查询结果 - TTL 1小时
- 端口扫描结果 - TTL 24小时
- GitHub 仓库元数据 - TTL 6小时
- 用户会话数据 - TTL 30分钟

**具体工作**:
- [ ] 为 DNS 查询服务添加缓存
- [ ] 为端口扫描服务添加缓存
- [ ] 为 GitHub 监控服务添加缓存
- [ ] 实现缓存失效机制
- [ ] 添加缓存统计和监控

#### 任务 2.1.3: Redis 配置和部署
**目标**: 完善 Redis 配置

**具体工作**:
- [ ] 添加 Redis 配置到 `config.yaml.example`
- [ ] 更新 Docker Compose 配置
- [ ] 添加 Redis 健康检查
- [ ] 编写 Redis 部署文档

---

### 2.2 插件系统基础框架（第2周）

#### 任务 2.2.1: 设计插件接口规范
**目标**: 定义插件的标准接口

**插件类型**:
1. **扫描插件** - 自定义扫描逻辑
2. **导出插件** - 自定义数据导出格式
3. **告警插件** - 自定义告警方式
4. **分析插件** - 自定义数据分析逻辑

**插件基类设计**:
```python
# app/plugins/base.py
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class PluginInfo:
    """插件信息"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: str  # scan, export, alert, analyze


class PluginBase(ABC):
    """插件基类"""

    @abstractmethod
    def get_info(self) -> PluginInfo:
        """获取插件信息"""
        pass

    @abstractmethod
    def register(self, app: Any) -> None:
        """注册插件到应用"""
        pass

    @abstractmethod
    def unregister(self) -> None:
        """注销插件"""
        pass


class ScanPlugin(PluginBase):
    """扫描插件基类"""

    @abstractmethod
    def scan(self, target: str, options: Dict[str, Any]) -> Dict[str, Any]:
        """执行扫描"""
        pass

    @abstractmethod
    def get_supported_targets(self) -> List[str]:
        """获取支持的目标类型"""
        pass


class ExportPlugin(PluginBase):
    """导出插件基类"""

    @abstractmethod
    def export(self, data: List[Dict[str, Any]], format: str) -> bytes:
        """导出数据"""
        pass

    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """获取支持的导出格式"""
        pass


class AlertPlugin(PluginBase):
    """告警插件基类"""

    @abstractmethod
    def send_alert(self, message: str, level: str, details: Dict[str, Any]) -> bool:
        """发送告警"""
        pass

    @abstractmethod
    def get_supported_levels(self) -> List[str]:
        """获取支持的告警级别"""
        pass


class AnalyzePlugin(PluginBase):
    """分析插件基类"""

    @abstractmethod
    def analyze(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """分析数据"""
        pass

    @abstractmethod
    def get_analysis_types(self) -> List[str]:
        """获取支持的分析类型"""
        pass
```

#### 任务 2.2.2: 实现插件加载器
**目标**: 动态加载和管理插件

**具体工作**:
- [ ] 创建 `app/plugins/manager.py`
- [ ] 实现插件发现和加载
- [ ] 实现插件生命周期管理
- [ ] 添加插件配置管理

**插件管理器设计**:
```python
# app/plugins/manager.py
import os
import importlib
import json
from typing import Dict, List, Optional, Type
from pathlib import Path
from app.plugins.base import PluginBase, PluginInfo


class PluginManager:
    """插件管理器"""

    def __init__(self, plugin_dir: str = "app/plugins"):
        self.plugin_dir = Path(plugin_dir)
        self.plugins: Dict[str, PluginBase] = {}
        self.plugin_registry: Dict[str, Dict] = {}

    def discover_plugins(self) -> List[str]:
        """发现可用插件"""
        plugins = []
        if not self.plugin_dir.exists():
            return plugins

        for item in self.plugin_dir.iterdir():
            if item.is_dir() and not item.name.startswith('_'):
                plugin_file = item / "plugin.py"
                if plugin_file.exists():
                    plugins.append(item.name)
        return plugins

    def load_plugin(self, plugin_name: str) -> Optional[PluginBase]:
        """加载指定插件"""
        try:
            module_path = f"app.plugins.{plugin_name}.plugin"
            module = importlib.import_module(module_path)

            # 查找插件类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, PluginBase) and
                    attr != PluginBase):
                    plugin_instance = attr()
                    self.plugins[plugin_name] = plugin_instance
                    return plugin_instance

        except Exception as e:
            print(f"Failed to load plugin {plugin_name}: {e}")
        return None

    def load_all_plugins(self) -> None:
        """加载所有插件"""
        plugin_names = self.discover_plugins()
        for name in plugin_names:
            self.load_plugin(name)

    def register_all(self, app) -> None:
        """注册所有插件到应用"""
        for name, plugin in self.plugins.items():
            try:
                plugin.register(app)
                print(f"Plugin {name} registered successfully")
            except Exception as e:
                print(f"Failed to register plugin {name}: {e}")

    def get_plugin(self, name: str) -> Optional[PluginBase]:
        """获取指定插件"""
        return self.plugins.get(name)

    def get_plugins_by_type(self, plugin_type: str) -> List[PluginBase]:
        """按类型获取插件"""
        result = []
        for plugin in self.plugins.values():
            info = plugin.get_info()
            if info.plugin_type == plugin_type:
                result.append(plugin)
        return result

    def unload_plugin(self, name: str) -> bool:
        """卸载插件"""
        if name in self.plugins:
            try:
                self.plugins[name].unregister()
                del self.plugins[name]
                return True
            except Exception as e:
                print(f"Failed to unload plugin {name}: {e}")
        return False
```

#### 任务 2.2.3: 开发示例插件
**目标**: 创建示例插件作为参考

**具体工作**:
- [ ] 创建示例扫描插件 `app/plugins/example_scan/`
- [ ] 创建示例导出插件 `app/plugins/example_export/`
- [ ] 创建示例告警插件 `app/plugins/example_alert/`
- [ ] 编写插件开发文档

---

### 2.3 服务拆分准备（第3-4周）

#### 任务 2.3.1: 服务边界定义
**目标**: 明确服务拆分边界

**服务划分**:
1. **Web API 服务** - 处理 HTTP 请求
2. **任务调度服务** - 管理扫描任务
3. **DNS 解析服务** - DNS 查询和解析
4. **端口扫描服务** - 端口扫描和指纹识别
5. **数据处理服务** - 数据清洗和存储
6. **监控告警服务** - 系统监控和告警

**具体工作**:
- [ ] 定义服务接口
- [ ] 设计数据交换格式
- [ ] 规划服务间通信方式
- [ ] 创建服务目录结构

#### 任务 2.3.2: API 网关设计
**目标**: 设计统一的 API 入口

**具体工作**:
- [ ] 设计 API 路由规则
- [ ] 实现请求转发
- [ ] 添加认证中间件
- [ ] 实现限流和熔断

#### 任务 2.3.3: 服务间通信
**目标**: 实现服务间通信机制

**通信方式**:
- 同步: HTTP REST API
- 异步: RabbitMQ / Redis Pub-Sub

**具体工作**:
- [ ] 创建 HTTP 客户端封装
- [ ] 实现消息队列封装
- [ ] 添加服务发现机制
- [ ] 实现重试和容错

---

## 目录结构

```
app/
├── plugins/                    # 插件系统
│   ├── __init__.py
│   ├── base.py                # 插件基类
│   ├── manager.py             # 插件管理器
│   ├── example_scan/          # 示例扫描插件
│   │   ├── __init__.py
│   │   └── plugin.py
│   ├── example_export/        # 示例导出插件
│   │   ├── __init__.py
│   │   └── plugin.py
│   └── example_alert/         # 示例告警插件
│       ├── __init__.py
│       └── plugin.py
├── services/                  # 服务层
│   ├── __init__.py
│   ├── dns_service.py         # DNS 服务
│   ├── scan_service.py        # 扫描服务
│   ├── task_service.py        # 任务服务
│   └── monitor_service.py     # 监控服务
├── utils/
│   ├── redis_utils.py         # Redis 工具
│   └── ...existing files
├── api/                       # API 层
│   ├── __init__.py
│   ├── gateway.py             # API 网关
│   └── v1/                    # API 版本 1
│       ├── __init__.py
│       ├── routes/
│       └── schemas/
└── config/
    ├── __init__.py
    ├── settings.py            # 配置管理
    └── services.py            # 服务配置
```

---

## 技术选型

### Redis 缓存
- **客户端**: redis-py
- **序列化**: JSON
- **连接池**: redis.ConnectionPool
- **集群支持**: redis-py-cluster (可选)

### 插件系统
- **加载方式**: importlib 动态导入
- **配置格式**: JSON / YAML
- **隔离性**: 独立命名空间
- **热加载**: importlib.reload

### 服务通信
- **同步**: httpx (异步 HTTP 客户端)
- **异步**: aio-pika (RabbitMQ)
- **服务发现**: 配置文件 (初期)

---

## 风险评估

### 高风险
1. **Redis 单点故障** - 需要配置主从复制或集群
2. **插件兼容性问题** - 需要严格的版本管理
3. **服务间通信延迟** - 需要优化网络配置

### 中风险
1. **数据一致性** - 分布式事务处理复杂
2. **部署复杂度** - 需要容器化和编排工具
3. **测试难度** - 需要集成测试环境

### 低风险
1. **性能瓶颈** - 可以通过缓存缓解
2. **安全风险** - 可以通过认证和加密解决

---

## 成功指标

### 性能指标
- [ ] API 响应时间减少 30%
- [ ] 数据库查询减少 50%
- [ ] 系统吞吐量提升 2 倍

### 可维护性指标
- [ ] 插件开发时间 < 1天
- [ ] 新功能上线时间 < 1周
- [ ] 服务独立部署和扩展

### 稳定性指标
- [ ] 系统可用性 > 99.9%
- [ ] 故障恢复时间 < 5分钟
- [ ] 数据丢失率 = 0

---

## 进度跟踪

| 任务 | 状态 | 开始日期 | 完成日期 | 备注 |
|------|------|----------|----------|------|
| 2.1.1 Redis 基础设施 | ⏳ | - | - | |
| 2.1.2 缓存策略实现 | ⏳ | - | - | |
| 2.1.3 Redis 配置部署 | ⏳ | - | - | |
| 2.2.1 插件接口设计 | ⏳ | - | - | |
| 2.2.2 插件加载器 | ⏳ | - | - | |
| 2.2.3 示例插件 | ⏳ | - | - | |
| 2.3.1 服务边界定义 | ⏳ | - | - | |
| 2.3.2 API 网关设计 | ⏳ | - | - | |
| 2.3.3 服务间通信 | ⏳ | - | - | |

---

**创建时间**: 2026-06-12
**预计完成时间**: 2026-07-10
**项目优先级**: 高
**资源需求**: 2-3名全职开发人员
