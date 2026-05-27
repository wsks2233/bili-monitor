# B站UP主动态监控 — 开发者指南

单包 Python 项目（src layout），hatchling 构建。B站 UP 主动态监控 + Flask Web 管理面板。

## 快速命令

```bash
pip install -e ".[dev]"                        # 安装（含 dev 依赖）
cp configs/example.yaml config.yaml             # 首次使用必须

bili-monitor monitor                            # 运行监控
bili-monitor monitor -v                         # 详细输出
bili-monitor web                                # Web (Flask, 默认 5000)
bili-monitor web --port 8000                    # 覆盖端口
python -m bili_monitor monitor                  # 等价入口

pytest                                          # 跑全部测试
pytest tests/test_storage/ -v                   # 单个模块
pytest --cov=bili_monitor                       # 覆盖率

black src/ tests/                               # 格式化
ruff check src/ tests/                          # lint
mypy src/                                       # 类型检查（仅 src）
```

## 关键架构

- 入口 `cli.py:main` → `monitor` / `web` 两个子命令，config 默认 `config.yaml`（`-c` 覆盖）
- API 层自带限流（1.5~3s 间隔）、WBI 签名、三次重试；Monitor 防检测随机间隔（0.9×~1.1× jitter）
- SQLite `data/bili_monitor.db`，首次自动建表，动态用 `dynamic_id` 去重
- 通知工厂 `create_notifier()` **大小写不敏感**，支持 `wechat` / `serverchan` / `pushplus` / `dingtalk` / `email` / `telegram`
- Web: Flask + CORS全开，`/api/status` 健康检查，`/api/events` SSE 实时推送，`/api/config` 可热更新 runtime 配置
- Cookie 服务将状态持久化到 `data/cookie_status.json`，30 分钟保活循环
- 图片下载 `images/{safe_upstream_name}/{dynamic_id}/`
- 日志 `logs/bili-monitor.log`，10MB 轮转 × 5 份

## 端口

代码默认 **5000**，Dockerfile/docker-compose 用 **8000**。`--port` 覆盖。

## Ruff 配置（pyproject.toml）

- line-length=120, target-version=py310, src=["src", "tests"]
- lint 选 E/W/F/I/N/UP，忽略 E501（交给 formatter）

## 代码约定

- 注释全部中文
- 日志命名空间 `bili-monitor`
- Type hints（3.10+），dataclass 定义模型，logging 代替 print
- 异常链不截断 `traceback.print_exc()`
- `conftest.py` 手动 `sys.path.insert(0, "src")`（虽然 pytest 配置有 pythonpath）
- `python-dotenv` 在依赖中但未被代码实际使用

## 注意

- config.yaml 含 Cookie 等敏感信息，已 `.gitignore`
- `bili-monitor` 命令由 `pyproject.toml` 的 `[project.scripts]` 注册，调用 `bili_monitor.cli:main`
- 通知器配置在 `notification` 数组，每种类型所需的字段不同（详见 `configs/example.yaml`）
