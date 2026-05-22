# B站UP主动态监控系统

一个功能完整的B站UP主动态监控系统，支持获取公开动态和充电专属动态，自动下载图片，数据持久化存储。

## 功能特性

- 动态获取：支持图文、视频、专栏、转发等多种动态类型
- 充电专属动态：支持获取需要充电权限的专属动态
- 图片下载：自动下载动态中的图片到本地
- 数据存储：SQLite数据库持久化
- 定时监控：可配置检查间隔，自动轮询
- 多UP主支持：支持同时监控多个UP主
- Cookie认证：支持配置Cookie访问授权内容
- WBI签名：自动处理B站API的WBI签名
- 通知推送：支持企业微信、钉钉、邮件、Telegram等通知方式
- Web管理：提供Web管理界面

## 安装

```bash
pip install .
```

## 使用

```bash
# 复制配置文件
cp configs/example.yaml config.yaml

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

## 许可证

MIT License
