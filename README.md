# B站UP主动态监控系统

一个功能完整的B站UP主动态监控系统，支持获取公开动态和充电专属动态，自动下载图片，数据持久化存储。

## 核心功能

| 功能 | 状态 | 说明 |
|------|------|------|
| 动态获取 | ✅ | 支持图文、视频、专栏、转发等多种动态类型 |
| 充电专属动态 | ✅ | 支持获取需要充电权限的专属动态 |
| 图片下载 | ✅ | 自动下载动态中的图片到本地 |
| 数据存储 | ✅ | SQLite/MySQL数据库持久化 |
| 定时监控 | ✅ | 可配置检查间隔，自动轮询 |
| 多UP主支持 | ✅ | 支持同时监控多个UP主 |
| Cookie认证 | ✅ | 支持配置Cookie访问授权内容 |
| WBI签名 | ✅ | 自动处理B站API的WBI签名 |
| 日志记录 | ✅ | 完整的日志系统，支持文件轮转 |

## 项目结构

```
bili-monitor/
├── bili_monitor/                 # 核心模块
│   ├── __init__.py              # 模块入口
│   ├── config.py                # 配置管理模块
│   ├── logger.py                # 日志模块
│   ├── models.py                # 数据模型定义
│   ├── bili_api.py              # B站API封装（含WBI签名）
│   ├── database.py              # 数据库存储模块
│   └── monitor.py               # 监控器核心逻辑
├── main.py                       # 主程序入口
├── view_dynamics.py              # 动态查看工具
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

## 模块详解

### 1. 配置模块 (config.py)

负责加载和解析YAML配置文件，支持以下配置项：

```python
@dataclass
class Config:
    monitor: MonitorConfig      # 监控配置
    upstreams: List[UpstreamConfig]  # UP主列表
    logger: LoggerConfig        # 日志配置
    database: DatabaseConfig    # 数据库配置
```

**配置项说明：**

| 配置项 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| monitor.check_interval | int | 300 | 检查间隔（秒） |
| monitor.retry_times | int | 3 | 重试次数 |
| monitor.retry_delay | int | 5 | 重试延迟（秒） |
| monitor.cookie | str | "" | B站Cookie |
| database.type | str | sqlite | 数据库类型 |
| database.path | str | data/bili_monitor.db | 数据库路径 |

### 2. API模块 (bili_api.py)

封装B站API调用，核心功能：

**API端点：**

| API | 用途 | 备注 |
|-----|------|------|
| `/x/polymer/web-dynamic/v1/feed/space` | 获取动态列表 | 需要WBI签名 |
| `/x/polymer/web-dynamic/v1/detail` | 获取动态详情 | 支持充电专属 |
| `/x/space/acc/info` | 获取用户信息 | - |
| `/x/relation/stat` | 获取粉丝数 | - |

**WBI签名机制：**
```python
def _sign_wbi(self, params: dict) -> dict:
    # 1. 获取img_key和sub_key
    # 2. 生成mixin_key
    # 3. 添加wts时间戳
    # 4. 参数排序并编码
    # 5. 计算w_rid签名
```

**动态类型映射：**

| 类型标识 | 类型名称 |
|----------|----------|
| DYNAMIC_TYPE_DRAW | 图文 |
| DYNAMIC_TYPE_AV | 投稿视频 |
| DYNAMIC_TYPE_ARTICLE | 专栏文章 |
| DYNAMIC_TYPE_FORWARD | 转发 |
| DYNAMIC_TYPE_WORD | 纯文字 |
| DYNAMIC_TYPE_OPUS | 图文动态 |

### 3. 数据模型 (models.py)

定义核心数据结构：

```python
@dataclass
class DynamicInfo:
    dynamic_id: str           # 动态ID
    uid: str                  # UP主UID
    upstream_name: str        # UP主名称
    dynamic_type: str         # 动态类型
    content: str              # 内容文本
    publish_time: datetime    # 发布时间
    images: List[ImageInfo]   # 图片列表
    video: VideoInfo          # 视频信息
    stat: StatInfo            # 互动数据
    raw_json: Dict            # 原始JSON

@dataclass
class ImageInfo:
    url: str                  # 图片URL
    width: int                # 宽度
    height: int               # 高度

@dataclass
class VideoInfo:
    bvid: str                 # BV号
    aid: int                  # AV号
    title: str                # 标题
    description: str          # 描述
    cover: str                # 封面

@dataclass
class StatInfo:
    like: int                 # 点赞数
    repost: int               # 转发数
    comment: int              # 评论数
```

### 4. 数据库模块 (database.py)

支持SQLite和MySQL两种数据库：

**数据库表结构：**

```sql
-- 动态表
CREATE TABLE dynamics (
    id INTEGER PRIMARY KEY,
    dynamic_id TEXT UNIQUE,
    uid TEXT,
    upstream_name TEXT,
    dynamic_type TEXT,
    content TEXT,
    publish_time TIMESTAMP,
    images TEXT,          -- JSON格式
    video TEXT,           -- JSON格式
    stat_like INTEGER,
    stat_repost INTEGER,
    stat_comment INTEGER,
    raw_json TEXT,        -- 原始JSON
    updated_at TIMESTAMP
);

-- UP主表
CREATE TABLE upstreams (
    id INTEGER PRIMARY KEY,
    uid TEXT UNIQUE,
    name TEXT,
    face TEXT,
    sign TEXT,
    level INTEGER,
    fans INTEGER,
    updated_at TIMESTAMP
);
```

### 5. 监控器 (monitor.py)

核心监控逻辑：

```python
class Monitor:
    def run(self):
        # 1. 初始化数据库
        # 2. 更新UP主信息
        # 3. 循环检查动态
        # 4. 下载图片
        # 5. 保存数据
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

#### SQLite 配置（默认，适合开发/测试）

```yaml
database:
  type: sqlite
  path: data/bili_monitor.db
```

#### MySQL 配置（推荐生产环境）

```yaml
database:
  type: mysql
  host: localhost
  port: 3306
  user: root
  password: your_password
  database: bili_monitor
```

**详细 MySQL 配置指南请查看：** [MYSQL_SETUP.md](MYSQL_SETUP.md)

**快速初始化 MySQL：**
```bash
# 创建数据库和表
python init_mysql.py

# 从 SQLite 迁移数据（可选）
python migrate_to_mysql.py
```

### 3. 运行

```bash
python main.py
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

## 扩展开发

### 添加通知功能

在 `monitor.py` 中实现 `_send_notification` 方法：

```python
def _send_notification(self, dynamic: DynamicInfo) -> None:
    # 实现微信、钉钉、邮件等通知
    pass
```

### 添加新的动态类型解析

在 `bili_api.py` 中扩展 `_extract_content_new` 方法：

```python
def _extract_content_new(self, modules: Dict[str, Any]) -> str:
    # 添加新的动态类型解析逻辑
    pass
```

### 切换到 MySQL

**快速迁移（3 步）：**

```bash
# 1. 测试 MySQL 连接
python test_mysql_connection.py

# 2. 初始化数据库
python init_mysql.py

# 3. 迁移数据（从 SQLite）
python migrate_to_mysql.py
```

**详细文档：**
- [MYSQL_QUICK_REFERENCE.md](MYSQL_QUICK_REFERENCE.md) - 快速参考
- [MYSQL_SETUP.md](MYSQL_SETUP.md) - 配置指南
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - 迁移指南

## API调用流程

```
┌─────────────────────────────────────────────────────────────┐
│                     获取动态流程                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. 尝试新版API (带WBI签名)                                  │
│     ├── 成功 → 解析动态列表                                  │
│     │   ├── 检查 is_only_fans 识别充电专属                   │
│     │   ├── 提取内容、图片、视频                             │
│     │   └── 返回动态列表                                     │
│     │                                                        │
│     └── 失败 → 切换备用方案                                  │
│         ├── 使用老版API获取动态ID列表                        │
│         └── 使用详情API逐个获取动态内容                      │
│                                                             │
│  2. 保存到数据库                                             │
│                                                             │
│  3. 下载图片到本地                                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 注意事项

1. **Cookie有效期**：Cookie会过期，需要定期更新配置文件中的Cookie
2. **API频率限制**：B站API有频率限制，建议检查间隔不低于60秒
3. **充电权益**：获取充电专属动态需要账号有有效的充电权益
4. **WBI签名**：新版API需要WBI签名，模块已自动处理

## 许可证

MIT License
