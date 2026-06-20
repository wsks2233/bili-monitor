# B站UP主动态监控系统

一个功能完整的B站UP主动态监控系统，支持获取多种动态类型，自动下载图片，通过多种渠道推送通知，并提供Web管理界面。

## 功能特性

- **动态获取**：支持图文、视频、专栏、转发、充电专属等多种动态类型
- **图片下载**：自动下载动态中的图片到本地
- **数据存储**：SQLite数据库持久化存储
- **定时监控**：可配置检查间隔，支持随机抖动防检测
- **多UP主支持**：同时监控多个UP主
- **Cookie认证**：支持Cookie访问授权内容，扫码登录自动刷新
- **WBI签名**：自动处理B站API的WBI签名校验
- **通知推送**：支持企业微信、钉钉、邮件、Telegram、PushPlus、Server酱等通知方式
- **Web管理**：提供Web管理界面，支持SSE实时推送
- **Docker部署**：支持Docker一键部署

## 安装

```bash
pip install .
```

## 快速开始

```bash
# 复制配置文件
cp config.example.yaml config.yaml

# 编辑配置文件，添加UP主和Cookie

# 运行监控
bili-monitor monitor

# 运行Web服务
bili-monitor web
```

## Docker部署

```bash
docker-compose up -d
```

## 开发

```bash
# 安装开发依赖
pip install -e ".[dev]"

# 运行测试
pytest

# 代码格式化
black src/ tests/

# 代码检查
ruff check src/ tests/
```

## 许可证

MIT License
