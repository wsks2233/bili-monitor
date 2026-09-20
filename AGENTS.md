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
pytest tests/test_config/test_models.py::TestX::test_y -v
pytest --cov=bili_monitor                       # 覆盖率

black src/ tests/                               # 格式化
ruff check src/ tests/                          # lint
mypy src/                                       # 类型检查（仅 src）
```

无 CI、无 pre-commit、无 Makefile。验证以本地 `pytest` / `ruff` / `black` 为准。

## 关键架构

- 入口 `src/bili_monitor/cli.py` → `bili-monitor`（`[project.scripts]`），子命令 `monitor` / `web`；根目录 `main.py` / `web_main.py` 只是薄包装
- 默认配置路径 **`config.yaml`（仓库根）**，模板是 **`config.example.yaml`**——没有 `configs/` 目录
- API 层 `api/client.py`：限流 1.5~3s、WBI 签名、tenacity 重试；Monitor 另有随机 jitter
- SQLite `data/bili_monitor.db`，原生 `sqlite3` + `check_same_thread=False`；表：`dynamics` / `upstreams` / `state`；`dynamic_id` 去重
- 通知工厂 `create_notifier()` **大小写不敏感**，类型：`wechat` / `serverchan` / `pushplus` / `dingtalk` / `email` / `telegram`；配置里 `notification` 是**列表**（可多个）
- Web：Flask 工厂 `create_app()` + 进程内 `EventBus`；CORS 全开；`/api/status` 健康检查；`/api/events` SSE；`/api/config` GET/POST 可热更配置
- Cookie 服务状态在 `data/cookie_status.json`，有 30 分钟保活循环
- 图片下载到 `images/{safe_upstream_name}/{dynamic_id}/`
- 日志 `logs/bili-monitor.log`（10MB × 5 轮转），logger 名 `bili-monitor`

## 端口 / Docker 陷阱

| 场景 | 端口 |
|------|------|
| 代码 / `config.yaml` 默认 `WebConfig.port` | **5000** |
| `Dockerfile` EXPOSE、`start.sh`、compose 映射 | **8000** |

- `start.sh` **同时**启动 `web --port 8000` 和 `monitor`
- Dockerfile 会尝试 `cp configs/docker.yaml`，但仓库里实际文件是根目录 **`config.docker.yaml`**；compose 则直接挂载 `./config.yaml`
- 需要本地跑 Web 时显式 `--port`，不要假设 8000

## 配置与敏感信息

- `config.yaml` / `data/` / `logs/` / `images/` 已 `.gitignore`；**含 Cookie、SMTP 授权码等，勿提交、勿写入日志/文档**
- `config.example.yaml` 注释里 Server酱/PushPlus 的示例 `type: wechat` 是错的——正确类型是 `serverchan` / `pushplus`
- 配置模型是**可变 dataclass**，运行时可直接改字段；`AppConfig.from_dict` 填默认值
- `python-dotenv` 在依赖里，**代码未使用**

## 测试

- 实际有测试的模块：`tests/test_api`、`test_config`、`test_cookie`、`test_notification`、`test_storage`
- `tests/test_web/`、`tests/test_monitor/` 只有空 `__init__.py`，没有测试用例
- `pyproject.toml`：`testpaths=["tests"]`，`pythonpath=["src"]`；`conftest.py` 也会手动 insert `src`
- 存储测试用临时 SQLite 文件 fixture，不依赖真实 `data/` 数据库

## 工具链 / 风格

- Python **≥3.10**；Type hints；注释与日志文案基本为中文
- `black` + `ruff`，**line-length=120**；ruff 选 `E/W/F/I/N/UP`，忽略 `E501`
- 异常处理保留完整 traceback（`traceback.print_exc()`）
- 依赖单一来源是 `pyproject.toml`；`requirements.txt` 与其大致对齐但不保证完整

## 不要踩的坑

- **不要相信 `docs/PROJECT_STRUCTURE.md`**：仍描述旧结构（`core/`、FastAPI、`bili_api.py`），与当前 `src/bili_monitor/` 不符
- 架构细节以 `CLAUDE.md` 与源码为准
- 配置示例路径是 `config.example.yaml`，不是 `configs/example.yaml`
- 新增通知类型：在 `notification/` 加实现类 + 注册到 `create_notifier()` 工厂，不要在 Monitor 里硬编码分支
- Web 路由在 `web/routes/` 各 Blueprint；健康检查/静态页/SSE 在 `web/app.py` 工厂里内联注册
