# B站UP主动态监控系统 — 开发者指南

## 项目概览

B站UP主动态监控 + Web管理面板。采用标准 Python 项目结构（src layout），使用 `pyproject.toml` 管理依赖。

## 快速命令

```bash
# 安装依赖
pip install -e ".[dev]"

# 复制配置文件
cp configs/example.yaml config.yaml

# 运行监控
bili-monitor monitor                    # 命令行监控
bili-monitor monitor -v                 # 详细输出
bili-monitor web                        # Web 管理 (Flask, 默认端口5000)
bili-monitor web --port 8000            # 指定端口

# 或使用 python -m
python -m bili_monitor monitor
python -m bili_monitor web

# 运行测试
pytest                                  # 运行所有测试
pytest tests/test_config/               # 运行特定模块测试
pytest -v                               # 详细输出
```

## 项目结构

```
bili-monitor/
├── pyproject.toml              # 项目配置和依赖
├── src/
│   └── bili_monitor/
│       ├── __init__.py
│       ├── __main__.py         # python -m 入口
│       ├── cli.py              # CLI 入口
│       │
│       ├── config/             # 配置管理
│       │   ├── models.py       # 配置模型（dataclass）
│       │   └── loader.py       # YAML 加载/保存
│       │
│       ├── api/                # B站 API 层
│       │   ├── client.py       # HTTP 客户端（统一限流）
│       │   ├── wbi.py          # WBI 签名（独立模块）
│       │   └── endpoints.py    # API 端点封装
│       │
│       ├── cookie/             # Cookie 管理
│       │   ├── validator.py    # 格式验证
│       │   ├── checker.py      # 有效性检查
│       │   └── service.py      # 保活 + 扫码登录
│       │
│       ├── monitor/            # 监控核心
│       │   ├── runner.py       # 监控循环
│       │   └── image.py        # 图片下载
│       │
│       ├── storage/            # 存储层
│       │   └── database.py     # SQLite 操作
│       │
│       ├── notification/       # 通知系统
│       │   ├── base.py         # 基类
│       │   ├── wechat.py       # 企业微信
│       │   ├── serverchan.py   # Server酱
│       │   ├── pushplus.py     # PushPlus
│       │   ├── dingtalk.py     # 钉钉
│       │   ├── email.py        # 邮件
│       │   └── telegram.py     # Telegram
│       │
│       └── web/                # Web 管理
│           ├── app.py          # Flask 应用工厂
│           └── routes/         # 路由蓝图
│               ├── config.py
│               ├── monitor.py
│               ├── dynamics.py
│               └── login.py
│
├── tests/                      # 测试
├── configs/                    # 配置文件
├── docs/                       # 文档
├── Dockerfile
└── docker-compose.yml
```

## 关键架构事实

- **入口点**：`cli.py`（统一入口），支持 `monitor` 和 `web` 子命令
- **核心模块**：
  - `config/` - 配置管理（dataclass 模型 + YAML 加载）
  - `api/` - B站 API（统一限流、WBI 签名独立模块）
  - `cookie/` - Cookie 管理（验证、检查、保活、登录）
  - `storage/` - SQLite 存储（INSERT OR IGNORE 防重复）
  - `notification/` - 通知系统（每种通知类型独立文件）
  - `monitor/` - 监控循环
  - `web/` - Flask Web 管理
- **Web框架**：Flask，CORS 全开，`/api/status` 是健康检查端点
- **配置**：`config.yaml`（可通过 `-c` 参数覆盖），Cookie 设在 `monitor.cookie`
- **数据库**：SQLite `data/bili_monitor.db`，首次启动自动建表
- **日志**：`logs/bili-monitor.log`，10MB 轮转 × 5 份
- **图片下载**：`images/{safe_upstream_name}/{dynamic_id}/`
- **Cookie 管理**：`cookie/service.py` 负责保活、扫码登录、过期回调
- **通知**：配置在 `config.yaml` 的 `notification` 数组，支持 `wechat` / `serverchan` / `pushplus` / `dingtalk` / `email` / `telegram`

## 端口注意

代码默认 Web 端口 **5000**，Dockerfile / docker-compose 用 **8000**。`bili-monitor web --port 8000` 可覆盖。

## 测试机制

使用 pytest，支持：
1. 单元测试（mock 外部依赖）
2. 集成测试（需要 config.yaml + 网络）

```bash
pytest                                  # 运行所有测试
pytest tests/test_config/               # 运行配置模块测试
pytest -v                               # 详细输出
pytest --cov=bili_monitor               # 代码覆盖率
```

## 开发工具

```bash
# 代码格式化
black src/ tests/

# 代码检查
ruff check src/ tests/

# 类型检查
mypy src/
```

## 风格约定

- 全部中文注释和输出
- 日志命名空间 `bili-monitor`
- 使用 type hints（Python 3.10+ 语法）
- 使用 dataclass 定义数据模型
- 使用 logging 模块（不使用 print）
- 异常链不截断（`traceback.print_exc()`）
