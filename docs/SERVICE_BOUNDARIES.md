# ARL 服务边界定义

## 概述

本文档定义了 ARL 项目服务拆分的服务边界、接口规范和数据交换格式。

---

## 服务划分

### 1. Web API 服务 (arl-web)

**职责**:
- 处理 HTTP 请求和响应
- 用户认证和授权
- 请求验证和参数解析
- 响应格式化和错误处理

**技术栈**:
- Flask + Flask-RESTX
- Gunicorn WSGI 服务器

**端口**: 5003

**依赖**:
- MongoDB (数据持久化)
- Redis (缓存)
- RabbitMQ (消息队列)

**API 版本**:
- `/api/v1/` - 当前版本
- `/api/` - 兼容旧版本

---

### 2. 任务调度服务 (arl-worker)

**职责**:
- 执行异步扫描任务
- 任务状态管理
- 任务结果存储
- 错误重试和日志记录

**技术栈**:
- Celery Worker
- RabbitMQ (消息代理)

**队列**:
- `arl_task` - 域名/IP 扫描任务
- `arl_github` - GitHub 监控任务

**依赖**:
- MongoDB (任务数据)
- Redis (缓存)

---

### 3. DNS 解析服务 (arl-dns)

**职责**:
- DNS 查询和解析
- DNS 记录缓存
- 批量 DNS 查询
- DNS 服务器管理

**技术栈**:
- Python + dnspython
- Redis (缓存)

**接口**:
```python
class DnsServiceInterface:
    def query_a(domain: str) -> List[str]
    def query_cname(domain: str) -> List[str]
    def query_mx(domain: str) -> List[str]
    def query_ns(domain: str) -> List[str]
    def query_txt(domain: str) -> List[str]
    def batch_query(domains: List[str], record_type: str) -> Dict[str, List[str]]
```

**依赖**:
- Redis (缓存)

---

### 4. 端口扫描服务 (arl-scan)

**职责**:
- TCP/UDP 端口扫描
- 服务指纹识别
- OS 检测
- 扫描结果分析

**技术栈**:
- Python + nmap
- Redis (缓存)

**接口**:
```python
class ScanServiceInterface:
    def scan_ports(target: str, ports: str, options: Dict) -> Dict
    def scan_os(target: str) -> Dict
    def scan_services(target: str, ports: List[int]) -> List[Dict]
    def batch_scan(targets: List[str], options: Dict) -> List[Dict]
```

**依赖**:
- Redis (缓存)
- MongoDB (扫描结果)

---

### 5. 数据处理服务 (arl-data)

**职责**:
- 数据清洗和标准化
- 数据聚合和统计
- 数据导入和导出
- 数据备份和恢复

**技术栈**:
- Python + pandas
- MongoDB (数据持久化)

**接口**:
```python
class DataServiceInterface:
    def clean_data(data: List[Dict], data_type: str) -> List[Dict]
    def aggregate_data(data: List[Dict], group_by: str) -> Dict
    def export_data(data: List[Dict], format: str, output_path: str) -> str
    def import_data(file_path: str, data_type: str) -> List[Dict]
```

**依赖**:
- MongoDB (数据持久化)

---

### 6. 监控告警服务 (arl-monitor)

**职责**:
- 系统监控和指标收集
- 告警规则管理
- 告警通知发送
- 日志聚合和分析

**技术栈**:
- Prometheus (指标收集)
- Grafana (可视化)
- Python (告警逻辑)

**接口**:
```python
class MonitorServiceInterface:
    def collect_metrics() -> Dict
    def check_alert_rules() -> List[Dict]
    def send_alert(alert: Dict, channels: List[str]) -> bool
    def get_system_status() -> Dict
```

**依赖**:
- Prometheus (指标存储)
- Redis (告警状态)

---

## 数据交换格式

### 1. 任务消息格式

```json
{
  "task_id": "uuid",
  "task_type": "domain_scan|ip_scan|github_monitor",
  "target": "example.com",
  "options": {
    "ports": "top_100",
    "scan_type": "syn",
    "timeout": 300
  },
  "priority": 5,
  "created_at": "2026-06-12T10:00:00Z",
  "retry_count": 0,
  "max_retries": 3
}
```

### 2. 扫描结果格式

```json
{
  "task_id": "uuid",
  "status": "completed|failed|running",
  "target": "example.com",
  "results": {
    "ips": ["1.2.3.4", "5.6.7.8"],
    "ports": [
      {"port": 80, "state": "open", "service": "http"},
      {"port": 443, "state": "open", "service": "https"}
    ],
    "os": "Linux 5.4",
    "services": [
      {"name": "nginx", "version": "1.18.0", "port": 80}
    ]
  },
  "started_at": "2026-06-12T10:00:00Z",
  "completed_at": "2026-06-12T10:05:00Z",
  "error": null
}
```

### 3. 告警消息格式

```json
{
  "alert_id": "uuid",
  "level": "info|warning|error|critical",
  "title": "Scan task failed",
  "message": "Task xxx failed after 3 retries",
  "details": {
    "task_id": "uuid",
    "target": "example.com",
    "error": "Connection timeout"
  },
  "created_at": "2026-06-12T10:00:00Z",
  "acknowledged": false
}
```

---

## 服务间通信

### 1. 同步通信 (HTTP REST API)

**使用场景**:
- 客户端到 Web API 服务
- Web API 服务到 DNS 解析服务
- Web API 服务到端口扫描服务

**协议**: HTTP/HTTPS
**数据格式**: JSON
**认证**: API Key (Header: `Token: xxx`)

**示例**:
```http
GET /api/v1/dns/query?domain=example.com&type=A
Host: arl-web:5003
Token: your-api-key
Content-Type: application/json

Response:
{
  "code": 200,
  "message": "success",
  "data": {
    "domain": "example.com",
    "type": "A",
    "records": ["1.2.3.4", "5.6.7.8"],
    "cached": true
  }
}
```

### 2. 异步通信 (消息队列)

**使用场景**:
- Web API 服务到任务调度服务
- 任务调度服务到 DNS 解析服务
- 任务调度服务到端口扫描服务
- 监控告警服务到通知服务

**协议**: AMQP (RabbitMQ)
**数据格式**: JSON
**队列**:
- `arl_task` - 扫描任务队列
- `arl_github` - GitHub 监控队列
- `arl_alert` - 告警通知队列

**示例**:
```python
# 发送任务
channel.basic_publish(
    exchange='',
    routing_key='arl_task',
    body=json.dumps(task_message),
    properties=pika.BasicProperties(
        delivery_mode=2,  # 持久化
        priority=5
    )
)
```

### 3. 缓存通信 (Redis)

**使用场景**:
- 所有服务到 Redis 缓存
- 会话数据共享
- 实时状态同步

**协议**: Redis Protocol
**数据格式**: JSON (序列化)

**缓存键规范**:
```
dns:{type}:{domain}           # DNS 查询缓存
scan:{target}:{ports}         # 扫描结果缓存
session:{session_id}          # 会话数据
task:{task_id}:status         # 任务状态
```

---

## 服务目录结构

```
arl/
├── docker-compose.yml              # Docker 编排配置
├── docker/
│   ├── Dockerfile.web              # Web API 服务镜像
│   ├── Dockerfile.worker           # 任务调度服务镜像
│   ├── Dockerfile.dns              # DNS 解析服务镜像
│   ├── Dockerfile.scan             # 端口扫描服务镜像
│   ├── Dockerfile.data             # 数据处理服务镜像
│   └── Dockerfile.monitor          # 监控告警服务镜像
├── app/
│   ├── __init__.py
│   ├── main.py                     # Web API 入口
│   ├── config.py                   # 配置管理
│   ├── api/                        # API 层
│   │   ├── __init__.py
│   │   ├── v1/                     # API v1
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── task.py
│   │   │   │   ├── domain.py
│   │   │   │   ├── ip.py
│   │   │   │   └── ...
│   │   │   └── schemas/
│   │   │       ├── task.py
│   │   │       ├── domain.py
│   │   │       └── ...
│   │   └── v2/                     # API v2 (未来)
│   ├── services/                   # 服务层
│   │   ├── __init__.py
│   │   ├── dns_service.py          # DNS 服务
│   │   ├── scan_service.py         # 扫描服务
│   │   ├── task_service.py         # 任务服务
│   │   ├── data_service.py         # 数据服务
│   │   └── monitor_service.py      # 监控服务
│   ├── workers/                    # Celery Worker
│   │   ├── __init__.py
│   │   ├── celery_app.py
│   │   ├── dns_worker.py           # DNS 解析 Worker
│   │   ├── scan_worker.py          # 端口扫描 Worker
│   │   └── github_worker.py        # GitHub 监控 Worker
│   ├── models/                     # 数据模型
│   │   ├── __init__.py
│   │   ├── task.py
│   │   ├── domain.py
│   │   ├── ip.py
│   │   └── ...
│   ├── utils/                      # 工具函数
│   │   ├── __init__.py
│   │   ├── redis_utils.py
│   │   ├── mongo_utils.py
│   │   └── ...
│   └── plugins/                    # 插件系统
│       ├── __init__.py
│       ├── base.py
│       ├── manager.py
│       └── ...
├── config/
│   ├── config.yaml                 # 主配置
│   ├── services.yaml               # 服务配置
│   └── logging.yaml                # 日志配置
├── tests/                          # 测试
│   ├── test_api/
│   ├── test_services/
│   ├── test_workers/
│   └── ...
└── docs/
    ├── API.md
    ├── SERVICES.md
    └── DEPLOYMENT.md
```

---

## 服务依赖关系

```
┌─────────────────────────────────────────────────────────────┐
│                        Web API 服务                          │
│                     (arl-web:5003)                           │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│   DNS 解析服务    │ │  端口扫描服务     │ │  数据处理服务     │
│   (arl-dns)      │ │  (arl-scan)      │ │  (arl-data)      │
└──────────────────┘ └──────────────────┘ └──────────────────┘
              │               │               │
              └───────────────┼───────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      消息队列 (RabbitMQ)                     │
│                     (arl-rabbitmq:5672)                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     任务调度服务                              │
│                     (arl-worker)                             │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │
              ▼               ▼               ▼
┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
│     MongoDB      │ │      Redis       │ │   监控告警服务    │
│  (arl-mongodb)   │ │   (arl-redis)    │ │  (arl-monitor)   │
└──────────────────┘ └──────────────────┘ └──────────────────┘
```

---

## 部署策略

### 1. 单机部署（当前）

所有服务部署在一台机器上，使用 Docker Compose 编排。

**优点**: 简单、快速、资源消耗少
**缺点**: 单点故障、扩展性差

### 2. 多机部署（未来）

- Web API 服务: 2+ 实例（负载均衡）
- 任务调度服务: 2+ 实例（高可用）
- DNS 解析服务: 1+ 实例
- 端口扫描服务: 1+ 实例
- MongoDB: 副本集（3 节点）
- Redis: 哨兵模式（3 节点）
- RabbitMQ: 集群模式（3 节点）

---

## 迁移计划

### 第一阶段（当前）
- ✅ 引入 Redis 缓存层
- ✅ 插件系统基础框架
- ⏳ 服务边界定义

### 第二阶段（进行中）
- ⏳ 服务接口定义
- ⏳ API 网关设计
- ⏳ 服务间通信实现

### 第三阶段（未来）
- ⏳ 拆分 DNS 解析服务
- ⏳ 拆分端口扫描服务
- ⏳ 完善监控告警服务

---

**创建时间**: 2026-06-12
**更新时间**: 2026-06-12
