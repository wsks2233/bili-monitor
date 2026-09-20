# B站UP主动态监控系统 — 项目结构

> 以本文与源码为准。历史上的 `core/`、FastAPI、`bili_api.py` 布局已废弃。

## 目录布局

```
bili-monitor/
├── src/bili_monitor/           # 主包（src layout，hatchling）
│   ├── cli.py                  # CLI：bili-monitor monitor|web
│   ├── __main__.py             # python -m bili_monitor
│   ├── api/                    # B站 HTTP + WBI + 动态解析
│   │   ├── client.py           # 限流、重试、设备 Cookie
│   │   ├── endpoints.py        # API 封装与 DynamicInfo 等模型
│   │   └── wbi.py              # WBI 签名
│   ├── config/                 # YAML ↔ 可变 dataclass
│   │   ├── loader.py
│   │   └── models.py
│   ├── cookie/                 # Cookie 校验 / 扫码 / 保活
│   ├── monitor/                # 轮询主循环 + 图片下载
│   │   ├── runner.py
│   │   └── image.py
│   ├── notification/           # 工厂 + 6 渠道通知
│   ├── storage/
│   │   ├── database.py         # SQLite（dynamics / upstreams；state 预留）
│   │   └── lock.py             # 监控单实例文件锁
│   └── web/                    # Flask 应用
│       ├── app.py              # 工厂 + EventBus SSE + status
│       ├── auth.py             # 可选 API Token
│       ├── deps.py             # Web 层读库（不依赖进程内 Monitor）
│       ├── routes/             # config / dynamics / login / monitor
│       └── static/index.html   # Vue3 + Element Plus 管理界面
├── tests/
│   ├── test_api/               # WBI、client 限流
│   ├── test_config/            # 配置模型与 cookie 字段保留
│   ├── test_cookie/
│   ├── test_monitor/           # baseline、use_ssl
│   ├── test_notification/
│   ├── test_storage/           # Database、ProcessLock、images_base
│   └── test_web/               # 配置密钥合并、独立读库、Token 鉴权
├── docs/
│   ├── PROJECT_STRUCTURE.md    # 本文件
│   ├── compose/spec/           # compose-next 功能 Spec
│   ├── EMAIL_SETUP_GUIDE.md
│   └── QUICK_EMAIL_SETUP.md
├── config.example.yaml         # 配置模板（仓库根，无 configs/ 目录）
├── config.docker.yaml          # Docker 默认配置模板
├── main.py / web_main.py / start_monitor.py   # 薄包装入口
├── setup_email.py              # 交互式邮件配置辅助
├── Dockerfile / start.sh / docker-compose.yml
├── pyproject.toml              # 依赖与工具配置的单一来源
└── requirements.txt            # 与 pyproject 大致对齐
```

### 运行时生成（已 gitignore）

| 路径 | 说明 |
|------|------|
| `config.yaml` | 实际配置，含 Cookie / 通知密钥，**勿提交** |
| `data/` | SQLite、`cookie_status.json`、`bili_monitor.lock` |
| `logs/` | `bili-monitor.log` 及轮转 |
| `images/` | 动态图片与 UP 主头像缓存（相对 **config 所在目录**） |

## 运行方式

```bash
pip install -e ".[dev]"
cp config.example.yaml config.yaml   # 编辑 Cookie / UP主 / 通知

bili-monitor monitor                 # 监控进程（文件锁防双开）
bili-monitor web                     # Web，默认端口 5000
bili-monitor web --port 8000

pytest
ruff check src/ tests/
```

## 端口与进程

- 本地代码默认 Web **5000**；Docker / `start.sh` 默认 **8000**（`WEB_PORT`）
- `start.sh` 默认只启动 Web；监控由 UI「启动」或 `START_MONITOR=1` / 另开 `bili-monitor monitor`
- 单实例锁：`data/bili_monitor.lock`（内容为 PID）

## 架构要点

- **数据源是 SQLite**：Web 读接口可在无 `MONITOR_INSTANCE` 时直读库
- **通知工厂** `create_notifier()`：`wechat` / `serverchan` / `pushplus` / `dingtalk` / `email` / `telegram`
- **配置 API**：GET 敏感字段掩码为 `******`；POST 缺键保留磁盘、掩码占位保留现值、`__CLEAR__` 显式清空
- **可选鉴权**：`web.auth_token` 或环境变量 `BILI_MONITOR_TOKEN`；写 API 与 `/api/logs` 需 token
- **首跑 baseline**：`monitor.seed_baseline`（默认 true）空库只入库不通知
