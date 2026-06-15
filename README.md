# ARL — Asset Reconnaissance Lighthouse / 资产侦察灯塔

[![Python](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)
[![Tests](https://img.shields.io/badge/tests-200%20passed-brightgreen.svg)](tests/)

> **本项目基于原 [TophantTechnology/ARL](https://github.com/TophantTechnology/ARL)（已删除）社区备份版修改。**  
> 在原始 ARL 基础上进行了架构重构、安全加固和性能优化，详细改动见下方说明。  
> *This project is a modified version of the community backup of the original [TophantTechnology/ARL](https://github.com/TophantTechnology/ARL) (now deleted).*

ARL（资产侦察灯塔）是一个轻量级资产侦察系统，用于快速发现与目标关联的互联网资产，构建基础资产信息库。适用于安全团队资产梳理和渗透测试前期侦察阶段。

ARL is a lightweight asset reconnaissance system for rapid discovery of internet-facing assets associated with targets. Designed for security team asset inventory and penetration testing reconnaissance phases.

---

## 功能特性 / Features

- **域名资产发现** — 子域名爆破、DNS 查询、证书透明度、搜索引擎、DNS 字典智能生成
- **IP 资产整理** — IP 段扫描、端口扫描（Top 10/100/1000/全端口）、服务识别、操作系统识别
- **WEB 站点识别** — 指纹识别、站点截图、文件泄漏检测、Host 碰撞检测
- **风险检测** — nuclei PoC 调用、WebInfoHunter JS 信息收集
- **任务调度** — 计划任务、周期监控、资产分组管理
- **消息推送** — 钉钉、飞书、企业微信、邮件、WebHook
- **GitHub 监控** — 关键字监控敏感信息泄漏
- **数据导出** — XLSX / JSON 格式，可插拔扩展

---

## 系统架构 / Architecture

```
Web UI / API -> Flask (app/main.py) -> Celery Worker (app/celerytask.py)
                                              |
                                    MongoDB (数据存储 / Storage)
                                              |
                                  RabbitMQ (任务队列 / Task Queue)
```

| 层 / Layer | 技术栈 / Stack | 说明 |
|-------------|---------------|------|
| Web | Flask + flask-restx | REST API + Swagger 文档 |
| 任务队列 | Celery + RabbitMQ | 异步任务分发，双队列（资产/GitHub） |
| 数据库 | MongoDB 4.0+ | 任务、资产、站点、证书等集合 |
| 缓存 | Redis (可选) | L1 进程内 LRU + L2 Redis 多级缓存 |
| 安全 | bcrypt + CSP + SSRF 防护 + NoSQL 注入防护 | 全局 MongoSanitizer |

---

## 快速开始 / Quick Start

### 环境要求 / Requirements

- **操作系统**: Linux (CentOS 7/8, Rocky 8, Ubuntu 20.04+)
- **Python**: 3.9+
- **服务依赖**: MongoDB 4.0+, RabbitMQ 3.13+, Redis 6.0+ (可选)
- **推荐配置**: CPU 4核, 内存 8GB, 带宽 10M

### 安装 / Installation

```bash
# 国际用户 / International
wget https://raw.githubusercontent.com/wqnmlgb151/ARL/master/misc/setup-arl.sh
chmod +x setup-arl.sh
./setup-arl.sh
```

### Docker 部署 / Docker

本项目**不提供预构建的 Docker 镜像**。如需使用 Docker 部署，请自行构建镜像：

This project does **NOT provide pre-built Docker images**. To deploy with Docker, build your own image:

```bash
# 构建 ARL 镜像 / Build ARL image
docker build -t arl:latest .

# 修改 docker-compose.yml 中的镜像名称为你构建的镜像
# Edit docker-compose.yml to use your built image name

# 启动服务 / Start services
cd docker
docker-compose up -d
```

> **注意**：`docker/docker-compose.yml` 中的 `tophant/arl` 镜像已不可用（原始项目已删除），部署前必须替换为自建镜像名。  
> *Note: The `tophant/arl` image in `docker/docker-compose.yml` is no longer available (original project deleted). Replace it with your own image name before deployment.*

### Web 访问 / Access

- **地址 / URL**: `https://IP:5003/`
- **API 文档 / API Docs**: `/api/doc`
- **默认账号 / Default Account**: `admin` / `arlpass`

---

## 开发命令 / Development Commands

```bash
# 启动开发服务器 / Start dev server
python app/main.py

# Celery Worker (资产任务 / asset tasks)
celery -A app.celerytask worker -Q arl_task -l info

# Celery Worker (GitHub 监控 / GitHub monitoring)
celery -A app.celerytask worker -Q arl_github -l info

# 调度器 / Scheduler
python -m app.scheduler

# 运行测试 / Run tests
pytest tests/unit/ -q

# 服务管理 (systemd) / Service management
systemctl status mongod rabbitmq-server arl-web arl-worker arl-scheduler nginx
```

---

## 配置说明 / Configuration

主要配置文件为 `app/config.yaml`（从 `app/config.yaml.example` 复制）。

| 配置项 | 说明 |
|--------|------|
| `MONGO.URI` | MongoDB 连接地址 |
| `CELERY.BROKER_URL` | RabbitMQ 连接地址 |
| `REDIS` | Redis 缓存配置 (可选) |
| `ARL.AUTH` | 是否开启 API 认证 |
| `ARL.BLACK_IPS` | SSRF 防护黑名单 |
| `ARL.PORT_TOP_10` | 自定义测试端口列表 |
| `FOFA.KEY` | FOFA API Key |
| `DINGDING` / `FEISHU` / `WXWORK` | 消息推送配置 |
| `GITHUB.TOKEN` | GitHub 搜索 Token |
| `PROXY.HTTP_URL` | HTTP 代理 |

---

## 安全特性 / Security

- **NoSQL 注入防护** — 所有数据库操作自动经过 `MongoSanitizer` 清洗
- **SSRF 防护** — 内置 IP 黑名单，阻止内网地址扫描
- **密码安全** — bcrypt 哈希存储，API Key 认证
- **HTTP 安全头** — CSP, X-Content-Type-Options, X-Frame-Options, HSTS
- **速率限制** — 可配置的 API 速率限制 (Flask-Limiter)
- **CSRF 保护** — API 端点 CSRF Token 验证

---

## 项目结构 / Project Structure

```
app/
├── main.py              # Flask 应用入口
├── config.py            # 配置管理 (YAML + 环境变量)
├── celerytask.py        # Celery 任务路由
├── scheduler.py         # 周期任务调度器
├── routes/              # API 路由 (30+ 端点)
├── services/            # 业务逻辑层 (侦察服务 + Service 类)
├── tasks/               # Celery 任务实现 (domain, ip, github, poc)
├── database/            # Repository 模式数据访问层
├── modules/             # 类型定义与错误码常量
├── utils/               # 工具函数 (DNS, IP, HTTP, Redis, 缓存)
├── middleware/           # 安全中间件 (CSP, CSRF, 限流)
├── dicts/               # 字典与数据文件 (端口列表, 错误码)
└── tools/               # 外部工具 (massdns, screenshot 等)
```

---

## 许可证 / License

MIT License. 详见 [LICENSE](LICENSE) 文件。

---

## 贡献者 / Contributors

[**wqnmlgb151**](https://github.com/wqnmlgb151)
