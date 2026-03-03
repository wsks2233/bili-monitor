# B站UP主动态监控系统

一个功能完整的B站UP主动态监控系统，支持获取公开动态和充电专属动态，自动下载图片，数据持久化存储。

## 核心功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 动态获取 | ✅ | 支持图文、视频、专栏、转发等多种动态类型 |
| 充电专属动态 | ✅ | 支持获取需要充电权限的专属动态 |
| 图片下载 | ✅ | 自动下载动态中的图片到本地 |
| 数据存储 | ✅ | SQLite数据库持久化 |
| 定时监控 | ✅ | 可配置检查间隔，自动轮询 |
| 多UP主支持 | ✅ | 支持同时监控多个UP主 |
| Cookie认证 | ✅ | 支持配置Cookie访问授权内容 |
| WBI签名 | ✅ | 自动处理B站API的WBI签名 |
| 日志记录 | ✅ | 完整的日志系统，支持文件轮转 |

## 项目结构

```
bili-monitor/
├── bili_monitor/                 # 核心模块
│   ├── api/                     # API模块
│   │   ├── bili_api.py         # B站API封装（含WBI签名）
│   │   ├── cookie_manager.py   # Cookie管理器
│   │   └── cookie_service.py   # Cookie服务
│   ├── core/                    # 核心模块
│   │   ├── config.py           # 配置管理
│   │   ├── logger.py           # 日志模块
│   │   └── models.py           # 数据模型
│   ├── notification/            # 通知模块
│   ├── storage/                 # 存储模块
│   │   └── database.py         # 数据库操作
│   ├── web/                     # Web界面
│   └── monitor.py               # 监控器核心逻辑
├── main.py                       # 主程序入口
├── web_main.py                   # Web服务入口
├── view_dynamics.py              # 动态查看工具
├── check_cookie.py               # Cookie检查工具
├── config.example.yaml           # 配置文件示例
├── requirements.txt              # 依赖包
├── data/                         # 数据目录
│   └── bili_monitor.db          # SQLite数据库
├── images/                       # 图片下载目录
│   └── {UP主名称}/
│       └── {动态ID}/
│           └── *.jpg
└── logs/                         # 日志目录
    └── bili-monitor.log
```

## 安装使用

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置

复制配置文件：
```bash
cp config.example.yaml config.yaml
```

编辑 `config.yaml`：
```yaml
# 监控配置
monitor:
  check_interval: 300      # 检查间隔（秒）
  retry_times: 3           # 重试次数
  retry_delay: 5           # 重试延迟（秒）
  cookie: ""               # B站Cookie（获取充电专属动态需要）

# UP主列表
upstreams:
  - uid: "546195"
    name: "老番茄"

# 日志配置
logger:
  level: INFO
  file: logs/bili-monitor.log

# 数据库配置
database:
  path: data/bili_monitor.db
```

### 3. 运行

```bash
# 启动监控
python main.py

# 启动Web服务
python web_main.py
```

### 4. 查看数据

```bash
# 查看UP主列表
python view_dynamics.py upstreams

# 查看动态列表
python view_dynamics.py list 1039025435 20

# 查看动态详情
python view_dynamics.py detail 1175108841806757890

# 在浏览器中打开动态
python view_dynamics.py open 1175108841806757890

# 导出动态到JSON
python view_dynamics.py export dynamics.json

# 交互式菜单
python view_dynamics.py
```

## 数据库表结构

### dynamics（动态表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| dynamic_id | TEXT | 动态ID（唯一） |
| uid | TEXT | UP主UID |
| upstream_name | TEXT | UP主名称 |
| dynamic_type | TEXT | 动态类型 |
| content | TEXT | 内容 |
| publish_time | TIMESTAMP | 发布时间 |
| images | TEXT | 图片列表（JSON） |
| video | TEXT | 视频信息（JSON） |
| stat_like | INTEGER | 点赞数 |
| stat_repost | INTEGER | 转发数 |
| stat_comment | INTEGER | 评论数 |
| raw_json | TEXT | 原始JSON |

### upstreams（UP主表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | INTEGER | 主键 |
| uid | TEXT | UP主UID（唯一） |
| name | TEXT | UP主名称 |
| face | TEXT | 头像URL |
| sign | TEXT | 签名 |
| level | INTEGER | 等级 |
| fans | INTEGER | 粉丝数 |

## 通知配置

支持多种通知方式：

```yaml
notification:
  # 企业微信机器人
  - type: wechat
    webhook_url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
  
  # 钉钉机器人
  - type: dingtalk
    webhook_url: "https://oapi.dingtalk.com/robot/send?access_token=xxx"
    secret: ""  # 可选，加签密钥
  
  # 邮件通知
  - type: email
    smtp_server: "smtp.qq.com"
    smtp_port: 465
    smtp_user: "xxx@qq.com"
    smtp_password: "授权码"
    sender: "xxx@qq.com"
    receivers:
      - "receiver@example.com"
  
  # Telegram Bot
  - type: telegram
    bot_token: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
    chat_id: "-1001234567890"
```

## Docker部署

```bash
# 构建镜像
docker build -t bili-monitor .

# 运行容器
docker run -d \
  --name bili-monitor \
  -p 8000:8000 \
  -v ./data:/app/data \
  -v ./logs:/app/logs \
  -v ./images:/app/images \
  -v ./config.yaml:/app/config.yaml \
  bili-monitor

# 或使用 docker-compose
docker-compose up -d
```

## 注意事项

1. **Cookie有效期**：Cookie会过期，需要定期更新配置文件中的Cookie
2. **API频率限制**：B站API有频率限制，建议检查间隔不低于60秒
3. **充电权益**：获取充电专属动态需要账号有有效的充电权益
4. **WBI签名**：新版API需要WBI签名，模块已自动处理

## 许可证

MIT License
