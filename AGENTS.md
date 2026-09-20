# B站UP主动态监控 — 开发者指南

单包 Python 项目（src layout），hatchling 构建。B站 UP 主动态监控 + Flask Web 管理面板。

## 快速命令

```bash
pip install -e ".[dev]"                        # 安装（含 dev 依赖）
cp config.example.yaml config.yaml              # 首次使用必须；路径在仓库根目录

bili-monitor monitor                            # 运行监控
bili-monitor monitor -v                         # 详细输出
bili-monitor web                                # Web (Flask, 默认 5000)
bili-monitor web --port 8000                    # 覆盖端口
python -m bili_monitor monitor                  # 等价入口

pytest                                          # 跑全部测试
pytest tests/test_storage/test_database.py -v   # 单个文件
pytest tests/test_web/test_config_and_dynamics.py -v
pytest --cov=bili_monitor                       # 覆盖率

black src/ tests/                               # 格式化
ruff check src/ tests/                          # lint
mypy src/                                       # 类型检查（仅 src）
```

无 CI、无 pre-commit、无 Makefile。验证以本地 `pytest` / `ruff` / `black` 为准。

## 关键架构

- 入口 `src/bili_monitor/cli.py` → `bili-monitor`（`[project.scripts]`），子命令 `monitor` / `web`；根目录 `main.py` 等是薄包装
- 配置模板 **`config.example.yaml`（仓库根）**，运行配置 **`config.yaml`**（gitignore）；**没有 `configs/` 目录**
- API 层 `api/client.py`：实例级限流 + `retry_times`/`retry_delay` 手动重试 + WBI；**不要写类属性 `RATE_LIMIT_CONFIG`**
- SQLite `data/bili_monitor.db` + `threading.RLock`；表 `dynamics` / `upstreams`（`state` 预留）；`dynamic_id` 去重
- 通知工厂 `create_notifier()`：`wechat` / `serverchan` / `pushplus` / `dingtalk` / `email` / `telegram`；`notification` 是列表
- Web：Flask + 可选 Token（`web.auth_token` 或 `BILI_MONITOR_TOKEN`）；`/api/status`、`/api/events` SSE、`/api/config`；读库不依赖进程内 Monitor（`web/deps.py`）
- 监控单实例锁：`data/bili_monitor.lock`；首跑 `seed_baseline` 默认只入库不通知
- 配置 POST：缺键保留磁盘 / 掩码保留密钥 / `__CLEAR__` 清空 / 明文覆盖
- 图片根目录与 **config 文件同级** `images/`
- 日志 `logs/bili-monitor.log`（10MB × 5），logger 名 `bili-monitor`

## 端口 / Docker

| 场景 | 端口 |
|------|------|
| 代码 / `config.yaml` 默认 | **5000** |
| Docker / `start.sh` / compose | **8000**（`WEB_PORT`） |

- `start.sh` **默认只启动 Web**；监控经 UI 启动或 `START_MONITOR=1` / 另开 `bili-monitor monitor`（有文件锁）
- Dockerfile 使用根目录 **`config.docker.yaml`**（已 COPY）；compose 挂载 `./config.yaml`

## 配置与敏感信息

- `config.yaml` / `data/` / `logs/` / `images/` 已 `.gitignore`；含 Cookie、SMTP 等，勿提交
- `config.example.yaml` 中 Server酱/PushPlus 的 `type` 为 **`serverchan` / `pushplus`**
- 配置模型是可变 dataclass；登录写 Cookie 应**原地改** `monitor.cookie`，勿整段重建
- 依赖以 `pyproject.toml` 为准（无 `python-dotenv` / `tenacity`）

## 测试

- 有测试：`tests/test_api`、`test_config`、`test_cookie`、`test_notification`、`test_storage`、`test_web`、`test_monitor`
- `pyproject.toml`：`testpaths=["tests"]`，`pythonpath=["src"]`
- 存储/ Web 测试用临时目录，不依赖真实 `data/` 或线上 B站 API

## 工具链 / 风格

- Python **≥3.10**；Type hints；注释与日志基本中文
- `black` + `ruff`，**line-length=120**；ruff 选 `E/W/F/I/N/UP`，忽略 `E501`
- 异常保留完整 traceback

## 不要踩的坑

- 文档与结构说明见 `docs/PROJECT_STRUCTURE.md`（已与源码对齐）与 `CLAUDE.md`
- 配置路径是仓库根的 `config.example.yaml`，不是 `configs/example.yaml`
- 新增通知类型：`notification/` 实现类 + 注册 `create_notifier()`
- 热更新限流必须写 `client.rate_limit_config`，不要碰 `RATE_LIMIT_CONFIG` 类 dict
- Web 写 API 在配置了 token 时需要 `X-Auth-Token` 或 `Authorization: Bearer`
- compose-next Spec：`docs/compose/spec/structure-and-features.md`
