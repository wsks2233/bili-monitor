# B站UP主动态监控系统

## 项目结构

```
bili-monitor/
├── bili_monitor/              # 主程序包
│   ├── api/                   # API接口层
│   │   ├── bili_api.py       # B站API封装
│   │   ├── cookie_manager.py # Cookie管理器
│   │   └── cookie_service.py # Cookie服务
│   ├── core/                  # 核心模块
│   │   ├── config.py         # 配置管理
│   │   ├── logger.py         # 日志系统
│   │   └── models.py         # 数据模型
│   ├── notification/          # 通知模块
│   │   ├── base.py           # 通知基类
│   │   ├── dingtalk.py       # 钉钉通知
│   │   ├── email.py          # 邮件通知
│   │   ├── telegram.py       # Telegram通知
│   │   └── wechat.py         # 微信通知
│   ├── storage/               # 数据存储
│   │   └── database.py       # SQLite数据库
│   ├── web/                   # Web界面
│   │   ├── static/           # 静态文件
│   │   └── app.py            # FastAPI应用
│   └── monitor.py            # 监控主逻辑
├── tests/                     # 测试套件
│   ├── __init__.py
│   ├── test_full.py          # 全面功能测试
│   └── test_monitor_run.py   # 监控流程测试
├── docs/                      # 文档目录
│   ├── EMAIL_SETUP_GUIDE.md  # 邮件配置指南
│   └── QUICK_EMAIL_SETUP.md  # 快速配置指南
├── config.example.yaml        # 配置示例
├── config.docker.yaml         # Docker配置示例
├── main.py                    # 主程序入口
├── web_main.py               # Web服务入口
├── start_monitor.py          # 快速启动脚本
├── setup_email.py            # 邮件配置工具
├── requirements.txt          # Python依赖
├── Dockerfile                # Docker构建文件
├── docker-compose.yml        # Docker编排文件
└── .gitignore                # Git忽略规则

# 运行时生成的目录（已被.gitignore忽略）
├── config.yaml               # 实际配置（包含敏感信息）
├── data/                     # 数据库文件
├── logs/                     # 日志文件
└── images/                   # 下载的图片
```

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置系统

复制配置文件并编辑：

```bash
cp config.example.yaml config.yaml
```

编辑 `config.yaml`，填入：
- B站Cookie（用于API访问）
- 要监控的UP主UID列表
- 通知方式（微信/邮件等）

### 3. 运行监控

**命令行模式：**
```bash
python main.py
```

**Web界面模式：**
```bash
python web_main.py
```
然后访问 http://localhost:8000

### 4. 运行测试

**全面功能测试：**
```bash
python tests/test_full.py
```

**监控流程测试（10秒）：**
```bash
python tests/test_monitor_run.py
```

## 功能特性

- ✅ 实时监控B站UP主动态更新
- ✅ 多平台通知支持（微信、邮件、钉钉、Telegram）
- ✅ Web管理界面
- ✅ Cookie自动保活
- ✅ 动态数据本地存储
- ✅ 图片自动下载
- ✅ 完善的错误处理和重试机制

## 文档

- [邮件推送配置指南](docs/EMAIL_SETUP_GUIDE.md)
- [快速配置文档](docs/QUICK_EMAIL_SETUP.md)

## 许可证

MIT License
