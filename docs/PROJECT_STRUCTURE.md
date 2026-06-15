# ARL项目结构文档

## 项目概述
ARL（Asset Reconnaissance Lighthouse）是一个现代化的资产侦察系统，用于快速发现与目标关联的互联网资产。

## 技术栈
- **后端**: Python 3.9+, Flask 2.2+, Celery 5.2+
- **数据库**: MongoDB 4.0+, Redis
- **前端**: 待升级到Vue.js
- **部署**: Docker, Docker Compose

## 目录结构

```
ARL/
├── app/                        # 主应用目录
│   ├── __init__.py            # 应用初始化
│   ├── __main__.py            # 主入口
│   ├── config.py              # 配置管理（已升级）
│   ├── celerytask.py          # Celery任务定义
│   ├── main.py                # Flask应用（已升级）
│   ├── scheduler.py           # 任务调度器
│   ├── config.yaml.example    # 配置文件示例
│   │
│   ├── modules/               # 数据模型定义
│   │   ├── __init__.py        # 常量定义
│   │   ├── baseInfo.py        # 基础信息
│   │   ├── domainInfo.py      # 域名信息
│   │   ├── ipInfo.py          # IP信息
│   │   ├── pageInfo.py        # 页面信息
│   │   └── wihRecord.py       # WIH记录
│   │
│   ├── routes/                # API路由定义
│   │   ├── __init__.py        # 路由注册
│   │   ├── task.py            # 任务相关API
│   │   ├── domain.py          # 域名相关API
│   │   ├── ip.py              # IP相关API
│   │   ├── site.py            # 站点相关API
│   │   └── ...                # 其他API
│   │
│   ├── services/              # 业务逻辑层
│   │   ├── __init__.py        # 服务注册
│   │   ├── commonTask.py      # 通用任务
│   │   ├── portScan.py        # 端口扫描
│   │   ├── fetchSite.py       # 站点获取
│   │   └── ...                # 其他服务
│   │
│   ├── tasks/                 # 任务实现层
│   │   ├── __init__.py        # 任务注册
│   │   ├── domain.py          # 域名任务
│   │   ├── ip.py              # IP任务
│   │   └── ...                # 其他任务
│   │
│   ├── utils/                 # 工具函数（已升级）
│   │   ├── __init__.py        # 核心工具函数
│   │   ├── type_defs.py       # 类型定义（新增）
│   │   ├── conn.py            # 数据库连接
│   │   ├── http.py            # HTTP工具
│   │   └── ...                # 其他工具
│   │
│   ├── helpers/               # 辅助函数
│   │   ├── task_schedule.py   # 任务调度辅助
│   │   ├── asset_site_monitor.py  # 资产站点监控
│   │   └── ...                # 其他辅助
│   │
│   ├── dicts/                 # 字典文件
│   │   ├── domain_dict_test.txt    # 测试域名字典
│   │   ├── domain_2w.txt           # 2万域名字典
│   │   ├── blackdomain.txt         # 黑名单域名
│   │   └── ...                     # 其他字典
│   │
│   └── tools/                 # 外部工具
│       ├── massdns            # DNS解析工具
│       ├── screenshot.js      # 截图脚本
│       └── driver.js           # 浏览器驱动
│
├── docker/                    # Docker部署配置
│   ├── docker-compose.yml     # Docker Compose配置
│   ├── config-docker.yaml     # Docker环境配置
│   ├── nginx.conf             # Nginx配置
│   └── worker/                # Worker配置
│
├── test/                      # 测试用例
│   ├── main.py                # 测试主入口
│   ├── test_domain.py         # 域名测试
│   ├── test_ip.py             # IP测试
│   └── ...                    # 其他测试
│
├── misc/                      # 杂项文件
│   ├── setup-arl.sh           # 安装脚本
│   ├── manage.sh              # 管理脚本
│   ├── arl-web.service        # Web服务配置
│   └── ...                    # 其他配置
│
├── docs/                      # 文档目录（新增）
│   ├── PROJECT_STRUCTURE.md   # 项目结构文档
│   ├── API.md                 # API文档
│   └── DEVELOPMENT.md         # 开发文档
│
├── tools/                     # 开发工具（新增）
│   ├── check_python39_compat.py  # Python兼容性检查
│   └── ...                    # 其他工具
│
├── requirements.txt           # Python依赖（已升级）
├── README.md                  # 项目说明
├── CHANGELOG.md               # 更新日志（待创建）
└── LICENSE                    # 许可证
```

## 核心模块说明

### 1. 配置管理 (`app/config.py`)
- 支持YAML配置文件
- 环境变量覆盖
- 类型安全的配置访问
- 自动创建必要目录

### 2. 类型定义 (`app/utils/type_defs.py`)
- 项目中所有类型注解定义
- 数据类定义（PortInfo, IPInfo, DomainInfo等）
- 枚举常量定义
- API响应类型定义

### 3. 工具函数 (`app/utils/__init__.py`)
- 文件操作工具
- 系统命令执行
- DNS解析
- IP/域名验证
- 日志管理

### 4. 任务调度 (`app/celerytask.py`)
- 异步任务处理
- 任务路由
- 错误处理
- 进度跟踪

### 5. 业务服务 (`app/services/`)
- 端口扫描服务
- 域名解析服务
- 站点获取服务
- 指纹识别服务

## API接口说明

### 认证方式
所有API请求需要在请求头中包含Token：
```
Authorization: Token your_api_key_here
```

### 主要API端点
- `/api/task/` - 任务管理
- `/api/domain/` - 域名管理
- `/api/ip/` - IP管理
- `/api/site/` - 站点管理
- `/api/user/` - 用户管理

详细API文档请参考 `/api/doc` 接口。

## 开发指南

### 环境要求
- Python 3.9+
- MongoDB 4.0+
- RabbitMQ 3.13+
- Redis 6.0+

### 安装步骤
1. 克隆仓库
2. 安装依赖: `pip install -r requirements.txt`
3. 复制配置文件: `cp app/config.yaml.example app/config.yaml`
4. 修改配置: 编辑 `app/config.yaml`
5. 启动服务: `python -m app.main`

### 代码规范
- 使用类型注解
- 遵循PEP 8规范
- 使用black格式化代码
- 编写单元测试

### 提交规范
- feat: 新功能
- fix: 修复bug
- refactor: 重构
- docs: 文档更新
- test: 测试
- chore: 构建/工具

## 部署指南

### Docker部署
```bash
cd docker
docker-compose up -d
```

### 源码部署
```bash
# 安装依赖
pip install -r requirements.txt

# 配置
cp app/config.yaml.example app/config.yaml

# 启动Web服务
python -m app.main

# 启动Worker
celery -A app.celerytask.celery worker -l info

# 启动调度器
python -m app.scheduler
```

## 测试
```bash
# 运行所有测试
cd test
python main.py

# 运行单个测试
python -m pytest test/test_domain.py
```

## 维护者
ARL Team - 安全社区贡献

## 许可证
详见LICENSE文件
