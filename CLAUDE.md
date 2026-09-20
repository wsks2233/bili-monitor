# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
python -m pytest tests/ -v

# Run a single test file
python -m pytest tests/test_storage/test_database.py -v
python -m pytest tests/test_web/test_config_and_dynamics.py -v

# Run tests with coverage
python -m pytest tests/ --cov=bili_monitor --cov-report=term

# Lint and format (ruff + black, line-length=120)
ruff check src/ tests/
black src/ tests/

# Run the monitor (CLI)
bili-monitor monitor

# Run the web UI (default port 5000; Docker uses 8000)
bili-monitor web

# Docker deployment
docker-compose up -d
```

## Project Architecture

Bilibili (B站) content creator monitoring system — polls for new posts (动态), downloads images, stores in SQLite, and sends multi-channel notifications.

### Source layout (`src/bili_monitor/`)

```
cli.py              — CLI entry (argparse, subcommands: monitor/web)
config/             — YAML config load/save, dataclass models (mutable)
api/                — HTTP client (instance rate-limit, manual retry), WBI, DynamicInfo parsing
cookie/             — Cookie validation, QR-code login, keepalive thread
monitor/            — Polling loop (baseline seed), image downloader
notification/       — Factory + wechat/serverchan/pushplus/dingtalk/email/telegram
storage/            — SQLite (dynamics, upstreams; state reserved) + ProcessLock
web/                — Flask factory, EventBus SSE, auth token, blueprints, static UI
```

### Key design decisions

- **Config models are mutable dataclasses** — in-place field updates preserve unrelated settings (e.g. cookie login must not reset jitter intervals).
- **API client** (`BiliHTTPClient`) wraps `requests.Session` with **instance-level** `rate_limit_config` and `retry_times`/`retry_delay` (not tenacity). Do not write the class attribute `RATE_LIMIT_CONFIG`.
- **Dynamic parsing** (`BiliEndpoints`) flattens B站 JSON into `DynamicInfo`. Polymer `web-dynamic/v1` with fallback to legacy `vc.bilibili.com`. DB stores **Chinese** type labels (`图文`, `投稿视频`, …).
- **Notifications** use `create_notifier()` (case-insensitive). Email `use_ssl` is part of `NotificationConfig` and passed only for `type: email`.
- **Web** Flask factory (`create_app()`) + `EventBus` SSE. Read APIs use `web/deps.get_database()` (Monitor instance or independent SQLite). Optional token auth via `web.auth_token` / `BILI_MONITOR_TOKEN`.
- **Database** raw `sqlite3`, `check_same_thread=False` **plus `threading.RLock`**. Images rooted at `{config_dir}/images`.
- **Single-instance monitor**: file lock `{data_dir}/bili_monitor.lock`; release on all exit paths.
- **Config POST contract**: missing key preserves disk; masked value (`******` / contains `...`) preserves secret; `__CLEAR__` wipes.

### Data flow

1. `Monitor.run()` acquires file lock, inits client/API/DB/cookie/notifiers
2. `_check_upstream()`: if no processed IDs and `seed_baseline`, save only (no notify)
3. New dynamics: `Database.save_dynamic()` → optional images → `Notifier.send()`
4. `on_event` → EventBus → `/api/events` SSE
5. Web UI reads via `/api/dynamics` etc. from SQLite (works without in-process Monitor)
