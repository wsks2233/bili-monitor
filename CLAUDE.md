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

# Run a single test class or test case
python -m pytest tests/test_web/test_app.py::TestCreateApp::test_config_api -v

# Run tests with coverage
python -m pytest tests/ --cov=src/bili_monitor --cov-report=term

# Lint and format (ruff + black, line-length=120)
ruff check src/ tests/
ruff format src/ tests/
black src/ tests/

# Run the monitor (CLI)
bili-monitor monitor

# Run the web UI
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
api/                — HTTP client (rate-limited, WBI-signed), endpoint wrappers, dynamic parsing
cookie/             — Cookie validation, QR-code login, keepalive thread
monitor/            — Main polling loop, image downloader
notification/       — Base class + implementations (wechat, dingtalk, email, telegram, pushplus, serverchan)
storage/            — SQLite database (dynamics, upstreams, state tables)
web/                — Flask factory + EventBus SSE + REST blueprint routes
```

### Key design decisions

- **Config models are mutable dataclasses** — fields can be modified directly at runtime without recreating objects.
- **API client** (`BiliHTTPClient`) wraps `requests.Session` with built-in rate limiting (1.5–3s jitter), auto-retry via tenacity, WBI signing, and device fingerprint cookies.
- **Dynamic parsing** (`BiliEndpoints`) translates B站's nested JSON into flat `DynamicInfo` objects. Falls back from the new polymer API (`web-dynamic/v1`) to the legacy `vc.bilibili.com` API on failure.
- **Notifications** use a factory (`create_notifier()`) mapping type strings to concrete classes, all sharing `format_message()` / `format_simple_message()` from the abstract base.
- **Web app** is a Flask factory (`create_app()`) with an in-process `EventBus` pushing SSE status updates to browser clients.
- **Database** uses raw `sqlite3` (no ORM) with `check_same_thread=False` for background monitor thread access.

### Data flow

1. `Monitor.run()` initializes components (HTTP client, API, DB, cookie service, notifiers)
2. Main loop calls `_check_all_upstreams()` → `_check_upstream()` per configured UP主
3. Each check calls `BiliEndpoints.get_user_dynamics()`, compares returned IDs against `Database.get_processed_ids()`
4. New dynamics: saved via `Database.save_dynamic()`, images downloaded via `ImageDownloader.download()`
5. Notifications sent to each configured `NotificationBase.send()` implementation
6. `_wait_for_next_check()` sleeps with jitter before next cycle
