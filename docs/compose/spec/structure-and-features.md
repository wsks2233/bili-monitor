---
feature: structure-and-features
status: in-progress
updated: 2026-03-20
branch: compose/structure-review
commits: 3e1c6cc..05d258e
---

# Structure & Features Remediation

## Report

**What was built（首批 P0 核心：T1–T4 + Review 修复）** — Web 读接口不再依赖进程内 `MONITOR_INSTANCE`：`web/deps.py` 的 `get_database()` 在无监控实例时按配置独立打开 SQLite，`/api/dynamics`、`/api/upstreams`、`/api/status` 可读库中已有数据。Monitor 增加基于 PID 文件的单实例锁（`storage/lock.py`），CLI 与 `POST /api/start` 共用；锁获取之后的工作全部包在 `try/finally` 中，启动失败或 Web 工作线程异常都会释放锁，避免活 PID 锁死后续启动。配置 API：GET 对 webhook/token/secret/cookie/smtp_password 等统一掩码为 `******`；POST 合并规则为「缺键保留磁盘 / 掩码占位保留现值 / `__CLEAR__` 显式清空 / 明文覆盖」，UI 原样回传 GET 载荷不再清空通知密钥；DingTalk `secret` 不再明文返回。

**Verification** — worktree `E:\demo\bili-monitor\.worktrees\structure-review`：`pytest tests/ -q` → **68 passed**（含锁互斥 monkeypatch、启动失败释锁、密钥保留/更新/`__CLEAR__`、缺键保留、无 Monitor 读库）。触达文件 `ruff check` 通过；全仓 ruff 仍有 **PRE-EXISTING** 历史风格问题（约 530 条，不在本批）。独立 Reviewer 两轮：首轮 CRITICAL 锁泄漏 + MAJOR 掩码/缺键清空/锁测试 → 已修；复审 **PASS**，无新增 CRITICAL/MAJOR。

**Journey log** — Windows 创建的 worktree 在 WSL 下 gitdir 解析失败，git 操作改用 PowerShell。`_mask_cookie` 中段 `...` 与 `_is_masked` 的 endswith 约定冲突，统一为 GET 固定 `******`。锁泄漏必须在 `runner.run` 与 Web worker 两处 `try/finally` 同时兜底。锁测试不能依赖真实外进程 PID，用 monkeypatch `_pid_alive` 证明互斥。配置 POST 必须「缺键 ≠ 空列表」，否则部分载荷会清空通知/UP主。

## [S1] Problem

软件主链路（拉动态 → 去重入库 → 下图 → 通知 → Web）在**同进程**可工作，但审阅发现一批会直接影响可用性、数据完整性与安全的问题：

1. **Web 读接口绑死进程内 Monitor**：`/api/dynamics`、`/api/upstreams` 在无 `MONITOR_INSTANCE` 时返回空数组，即使 SQLite 已有 CLI 监控写入的数据；`start.sh` 双进程部署下看板常空。
2. **双监控风险**：Docker/`start.sh` 同时跑 `monitor` 进程 + Web 进程，UI `POST /api/start` 再启一个 Monitor，可能双轮询、双通知。
3. **配置保存可清空通知密钥**：`GET /api/config` 将 webhook/token 掩码为 `...`，`POST` 丢弃以 `...` 结尾的字段后 `NotificationConfig(**n_dict)` 默认空串；UI 回传 GET 载荷导致密钥被写空（仅 `smtp_password=="******"` 特判恢复）。
4. **管理 API 无鉴权 + CORS 全开 + 默认 `0.0.0.0`**；DingTalk `secret` 在 GET 时明文返回。
5. **首跑通知洪水**：空库时近期动态全部 `save_dynamic` 成功并触发通知，无 baseline。
6. **Docker/端口/路径分裂**：Dockerfile 引用不存在的 `configs/docker.yaml`（实为 `config.docker.yaml` 且未 COPY）；代码默认 Web 端口 5000，Docker/start 用 8000；图片路径 CWD vs config 目录 vs DB 推导不一致。
7. **共享状态缺陷**：`BiliHTTPClient.RATE_LIMIT_CONFIG` 为类级 dict，实例赋值污染全进程；SQLite `check_same_thread=False` 且无锁。
8. **半成品与文档谎言**：`retry_times`/`retry_delay`/`state` 表/`use_ssl`/`tenacity`/`dotenv` 未真正接入；UI 类型筛选用 `DYNAMIC_TYPE_*` 而库中存中文；登录 API 不返回 `masked_cookie`；`docs/PROJECT_STRUCTURE.md` 与部分 CLAUDE/example/邮件文档过时或错误。

## [S2] Design

### 进程模型与数据访问

- **单一事实源是 SQLite**（`database.path`，默认 `data/bili_monitor.db`）。Web 读接口（`/api/dynamics`、`/api/upstreams`、`/api/status` 的统计部分）必须能**在无 Monitor 实例时**通过 `Database(config.database)` 读库；有 Monitor 时可继续用实例（结果应一致）。
- **监控单实例**：Monitor 启动（CLI `run_monitor` 与 Web `POST /api/start`）在 DB 路径旁获取文件锁（如 `data/bili_monitor.lock`，含 PID）；获取失败则报错退出/返回 409，避免双进程双通知。
- **推荐部署形态**（写入文档，不强制改产品）：
  - A：仅 CLI monitor + Web 只读看板（Web 不自动 start）；
  - B：仅 Web 进程内 start（`start.sh` 不再拉起 monitor）。
  `start.sh` 二选一实现，默认改为 **B**（Web 8000 + 内嵌监控由 UI/配置控制）或 **A**（只起 monitor，Web 另述）——首批落地时采用：**`start.sh` 只启动 web；监控通过 UI/`bili-monitor monitor` 单入口 + 文件锁**。
- **SSE `/api/status`**：无 Monitor 时仍返回 DB 统计与 `running:false`，不假装空库。

### 配置与密钥契约

- `GET /api/config`：所有敏感字段统一掩码（含 DingTalk `secret`、cookie、webhook、token、smtp_password）。掩码策略：保留前 2 + `...` + 后 2，或固定 `******`；**不得**回显完整密钥。
- `POST /api/config` 合并规则（与类型无关）：
  - 字段缺失、空串、或等于掩码占位（以 `...` 结尾 / `******`）→ **保留磁盘上现值**；
  - 提供新的非掩码明文 → 覆盖；
  - 显式传 `null` 或约定清空标记（如 `""` 仅当字段原就为空时）→ 按「保留」处理，避免误清空；若需清空，客户端必须传特殊值 `__CLEAR__`（文档化）。
- 合并按 **通知项对齐**：优先 `type` 匹配现配置中同 type 的第一项；否则按 index。重建 `NotificationConfig` 时从 `current_config.notification` 拷贝被保留字段。
- QR/直接写 Cookie 路径重建 `MonitorConfig` 时必须**保留**现有 `request_*` / `upstream_*` / `error_*` / `check_interval` 等抖动与间隔字段，只更新 `cookie`。
- `email.use_ssl`：进入 `NotificationConfig`（默认 `true`），`from_dict`/`save_config`/`create_notifier`/`EmailNotifier` 全链路传递。

### 限流与存储并发

- `BiliHTTPClient` 将 `RATE_LIMIT_CONFIG` 改为**实例属性**（`__init__` 中 `dict(...)` 拷贝类默认值），禁止写入类 dict。
- `Database` 增加进程内 `threading.Lock`，所有 cursor/commit 路径 `with self._lock`。

### 首跑 baseline

- Monitor 首次对某 `uid` 检查且库中 `get_processed_ids` 为空时：**只入库不通知**（或配置 `monitor.seed_baseline: true` 默认 true）；日志明确「baseline 模式，跳过 N 条历史」。
- 可选配置 `monitor.notify_on_seed: bool = false`。

### Docker 与路径

- Dockerfile：`COPY config.docker.yaml ./config.docker.yaml`，启动前若无用户 `config.yaml` 则复制为 `config.yaml`；删除错误的 `configs/docker.yaml` 分支。
- 端口：文档与 compose 保持容器 **8000**；本地代码默认 **5000** 不强制改；`start.sh` 使用 `WEB_PORT`（默认 8000）。
- 图片根目录统一函数：以 **config 文件所在目录** 为 base（`Path(config_path).parent / "images"`），Monitor/ImageDownloader/Web/DB 展示路径均使用同一解析（DB 层若只存相对路径，由 Web 层解析；Monitor 写入时用同一 base）。

### Web 安全基线

- `web.auth_token` 可选配置（或环境变量 `BILI_MONITOR_TOKEN`）。若非空：所有 **写操作**（POST `/api/config`、`/api/start`、`/api/stop`、`/api/login/cookie`）与 `/api/logs` 要求 `X-Auth-Token` 或 `Authorization: Bearer`；缺失/错误返回 401。读接口（status/dynamics/events/静态）保持开放以便内网看板。
- CORS：若配置了 token，限制为同源或配置的 `web.cors_origins`（默认 `[]` 表示不反射任意 Origin；无 token 时保持兼容但文档警告）。
- 默认绑定：无 token 时日志 WARNING「管理 API 无鉴权，勿暴露公网」。

### 前端修复契约

- 动态类型筛选：与库中存储一致，选项使用中文标签（来自 `DYNAMIC_TYPE_MAP` 值），或后端同时返回 `dynamic_type_code`；**首批**改前端选项为中文值。
- 登录 check 成功响应增加 `masked_cookie`（后端已掩码逻辑复用）。
- 通知类型 label 补全 serverchan/pushplus。
- 配置保存：前端不再原样回传 GET 掩码载荷中的密钥字段，或依赖后端合并契约（后端必须正确；前端同步）。

### 文档与死代码

- 重写 `docs/PROJECT_STRUCTURE.md` 对齐当前 `src/bili_monitor` + Flask。
- 修正 `CLAUDE.md`（重试描述、测试路径）、`config.example.yaml`（serverchan/pushplus type）、邮件文档 `use_ssl`。
- `retry_times`/`retry_delay`：要么在 `BiliHTTPClient` 手动重试循环中使用，要么标注废弃并从 example/UI 移除——**首批**接入 client 重试上限。
- 移除或接线：`tenacity`（接入则用，否则从依赖删除）；`python-dotenv` 从依赖删除（代码未用）。`state` 表保留建表但文档标明 reserved，或删除建表——首批 **保留建表 + 注释 reserved**，避免迁移风险。

### 测试边界

- 新增测试至少覆盖：配置 POST 密钥保留合并、限流实例隔离、baseline 跳过通知、文件锁互斥、Web 无 Monitor 时读 DB、use_ssl 传递。
- 不强制 E2E 打真实 B站 API；HTTP 层用 mock/本地 SQLite。

## [S3] Out of Scope

- 不引入 ORM、不换 Web 框架、不重构为微服务。
- 不做完整用户系统/OAuth；鉴权仅可选静态 token。
- 不改 B站 API 协议适配逻辑（除非缺陷直接导致上述问题）。
- 不删除根目录薄包装入口（`main.py` 等），仅文档说明。
- 不在本 Spec 承诺性能优化或监控告警平台化。
- 数据库 schema 大迁移、历史 `config.yaml` 自动转换工具不在首批。

## Tasks

### P0 — 正确性与安全基线（建议首批）

- [x] T1: Web 读接口改为可独立读 SQLite — acceptance: 无 `MONITOR_INSTANCE` 时 `/api/dynamics`、`/api/upstreams`、`/api/status` 能返回库中已有数据与统计；有 Monitor 时行为不回归。(covers: S2)
- [x] T2: Monitor 文件锁单实例 — acceptance: 第二次 CLI monitor 或 Web `/api/start` 在锁被占用时失败并明确报错；锁文件含 PID；进程正常退出释放锁。(covers: S2; depends: T1)
- [x] T3: 配置 GET/POST 密钥掩码与合并契约 — acceptance: GET 不返回完整 secret/webhook/token/cookie/password；POST 回传掩码值时磁盘配置密钥不变；新明文可更新；有单测。(covers: S2)
- [x] T4: DingTalk secret 纳入掩码 — acceptance: `GET /api/config` 中 `secret` 不为明文。(covers: S2; depends: T3)
- [ ] T5: 登录/写 Cookie 保留 Monitor 抖动配置字段 — acceptance: 保存 cookie 后 `request_min` 等仍为用户配置值而非重置默认。(covers: S2)
- [ ] T6: `BiliHTTPClient` 限流改为实例属性 — acceptance: 两个不同 rate 的 client 互不影响；有单测。(covers: S2)
- [ ] T7: `Database` 增加线程锁 — acceptance: 所有 DB 读写经锁；并发烟测不抛 sqlite 线程错误（可单测模拟）。(covers: S2)
- [ ] T8: Dockerfile/config.docker.yaml 与端口文档对齐 — acceptance: Docker 构建不再依赖不存在的 `configs/docker.yaml`；`start.sh`/README/AGENTS 端口说明一致（容器 8000，本地默认 5000）。(covers: S2)
- [ ] T9: 可选 API Token 鉴权 — acceptance: 配置 `web.auth_token` 或 env 后，未带 token 的写 API 返回 401；未配置时行为与现状兼容；文档说明。(covers: S2)
- [ ] T10: 图片路径统一到 config 目录 — acceptance: 同一 config 路径下 Monitor 下载与 Web `/images` 服务同一文件。(covers: S2)

### P1 — 功能缺陷

- [ ] T11: 首跑 baseline（只入库不通知） — acceptance: 空库首次轮询写入历史动态且不发送通知；日志有 baseline 说明；`notify_on_seed=true` 可恢复通知。(covers: S2; depends: T2)
- [ ] T12: 前端动态类型筛选与库内中文标签对齐 — acceptance: UI 筛选「图文」等能过滤出对应记录。(covers: S2; depends: T1)
- [ ] T13: `email.use_ssl` 全链路 — acceptance: 配置 false 时 `EmailNotifier` 走非 SSL 路径；example/文档一致；工厂传递参数。(covers: S2)
- [ ] T14: 登录 API 返回 `masked_cookie` + UI 使用 — acceptance: 扫码成功响应含 `masked_cookie`；UI 不再读 undefined。(covers: S2)
- [ ] T15: 通知类型 UI label 补全 serverchan/pushplus — acceptance: 配置页正确显示两种类型名称。(covers: S2)
- [ ] T16: 去掉重复的 `/api/logs` 注册 — acceptance: 仅保留一处实现（建议 `routes/monitor.py`），行为不变。(covers: S2)
- [ ] T17: `retry_times`/`retry_delay` 接入 HTTP 重试 — acceptance: client 按配置次数重试；example 与运行时一致；CLAUDE 不再写 tenacity 自动重试（若未接入 tenacity）。(covers: S2; depends: T6)

### P2 — 文档与清理

- [ ] T18: 重写 `docs/PROJECT_STRUCTURE.md` — acceptance: 描述当前 src 布局、Flask、真实测试目录，无 FastAPI/core 旧结构。(covers: S2)
- [ ] T19: 修正 `config.example.yaml` 通知 type 与 `CLAUDE.md`/`AGENTS.md` 关键事实 — acceptance: example 中 serverchan/pushplus type 正确；文档与代码一致。(covers: S2)
- [ ] T20: 依赖清理 — acceptance: `python-dotenv` 移除或文档标明 unused；`tenacity` 接入或移除；`pip install -e ".[dev]"` 与 pytest 仍通过。(covers: S2)
- [ ] T21: 邮件/setup 文档与 `use_ssl` 行为一致 — acceptance: 文档描述与 T13 实现一致。(covers: S2; depends: T13)

### 验证（贯穿）

- [x] T22: 全量本地验证 — acceptance: worktree 内 `pytest` 全绿；对首批改动有对应测试。首批 T1–T4：`pytest` **65 passed**；新增/触达文件 `ruff check` 通过；全仓 `ruff check src/ tests/` 存在 **PRE-EXISTING** 约 530 条历史风格问题（空白行/未用 import 等），不在本批范围。(covers: S2; depends: T1,T2,T3,T6,T7)
