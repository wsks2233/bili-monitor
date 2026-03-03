# MySQL 数据库配置指南

## 📋 目录

- [为什么使用 MySQL](#为什么使用-mysql)
- [快速开始](#快速开始)
- [配置说明](#配置说明)
- [数据库初始化](#数据库初始化)
- [数据迁移](#数据迁移)
- [常见问题](#常见问题)

---

## 🎯 为什么使用 MySQL

### SQLite vs MySQL

| 特性 | SQLite | MySQL |
|------|--------|-------|
| **并发性能** | 低（文件锁） | 高（行级锁） |
| **数据量** | < 10GB | 无限制 |
| **多用户访问** | 不支持 | 支持 |
| **备份恢复** | 文件复制 | 在线备份 |
| **适用场景** | 开发/测试 | 生产环境 |

### MySQL 优势

- ✅ **高并发**: 支持多个监控实例同时运行
- ✅ **大数据量**: 轻松存储数百万条动态
- ✅ **高可用**: 支持主从复制、集群
- ✅ **易维护**: 在线备份、性能监控
- ✅ **安全性**: 用户权限管理、数据加密

---

## 🚀 快速开始

### 1. 安装 MySQL

#### Windows
```bash
# 下载 MySQL Installer
https://dev.mysql.com/downloads/installer/

# 或使用 Chocolatey
choco install mysql
```

#### Linux (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install mysql-server
sudo mysql_secure_installation
```

#### Linux (CentOS/RHEL)
```bash
sudo yum install mysql-server
sudo systemctl start mysqld
sudo systemctl enable mysqld
```

#### Docker (推荐)
```bash
docker run -d \
  --name mysql-bili \
  -e MYSQL_ROOT_PASSWORD=your_password \
  -e MYSQL_DATABASE=bili_monitor \
  -p 3306:3306 \
  mysql:8.0
```

### 2. 创建数据库

```sql
CREATE DATABASE bili_monitor 
DEFAULT CHARACTER SET utf8mb4 
DEFAULT COLLATE utf8mb4_unicode_ci;
```

### 3. 创建用户（可选但推荐）

```sql
CREATE USER 'bili_monitor'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON bili_monitor.* TO 'bili_monitor'@'%';
FLUSH PRIVILEGES;
```

---

## ⚙️ 配置说明

### 编辑 config.yaml

```yaml
database:
  type: mysql
  host: localhost          # MySQL 服务器地址
  port: 3306              # MySQL 端口
  user: bili_monitor      # 数据库用户名
  password: your_password # 数据库密码
  database: bili_monitor  # 数据库名称
```

### 配置项说明

| 配置项 | 说明 | 默认值 | 示例 |
|--------|------|--------|------|
| `type` | 数据库类型 | sqlite | `mysql` |
| `host` | MySQL 服务器地址 | localhost | `192.168.1.100` |
| `port` | MySQL 端口 | 3306 | `3306` |
| `user` | 数据库用户名 | - | `bili_monitor` |
| `password` | 数据库密码 | - | `your_password` |
| `database` | 数据库名称 | - | `bili_monitor` |

---

## 🔧 数据库初始化

### 方法 1: 自动初始化（推荐）

```bash
# 1. 配置 config.yaml
# 2. 运行初始化脚本
python init_mysql.py
```

初始化脚本会：
- ✅ 创建数据库（如果不存在）
- ✅ 创建所有必要的表
- ✅ 创建索引
- ✅ 验证连接

### 方法 2: 手动初始化

```sql
-- 1. 创建数据库
CREATE DATABASE IF NOT EXISTS bili_monitor 
DEFAULT CHARACTER SET utf8mb4 
DEFAULT COLLATE utf8mb4_unicode_ci;

-- 2. 使用数据库
USE bili_monitor;

-- 3. 创建表（运行 database.py 中的建表语句）
```

### 方法 3: 程序自动创建

直接运行监控程序，数据库表会自动创建：

```bash
python main.py
```

---

## 📦 数据迁移

### 从 SQLite 迁移到 MySQL

#### 步骤 1: 准备工作

```bash
# 1. 确保 SQLite 数据库存在
ls data/bili_monitor.db

# 2. 配置 config.yaml 为 MySQL
# 3. 初始化 MySQL 数据库
python init_mysql.py
```

#### 步骤 2: 运行迁移脚本

```bash
python migrate_to_mysql.py
```

迁移脚本会：
- ✅ 读取 SQLite 数据
- ✅ 写入 MySQL 数据库
- ✅ 验证数据完整性
- ✅ 输出迁移报告

#### 步骤 3: 验证迁移

```bash
# 查看动态列表
python view_dynamics.py list

# 或使用 MySQL 客户端
mysql -u bili_monitor -p bili_monitor
SELECT COUNT(*) FROM dynamics;
SELECT COUNT(*) FROM upstreams;
```

#### 步骤 4: 切换数据库

确认迁移成功后：

```bash
# 1. 备份 SQLite 数据库
cp data/bili_monitor.db data/bili_monitor.db.backup

# 2. 修改 config.yaml
database:
  type: mysql
  # ... MySQL 配置

# 3. 重启监控程序
python main.py
```

---

## 🔍 常见问题

### Q1: 连接失败 "Can't connect to MySQL server"

**解决方案：**

1. 检查 MySQL 服务是否运行
```bash
# Windows
net start MySQL80

# Linux
sudo systemctl status mysql
```

2. 检查防火墙设置
```bash
# Linux
sudo ufw allow 3306/tcp
```

3. 检查用户权限
```sql
SELECT user, host FROM mysql.user;
```

### Q2: 字符集错误 "Incorrect string value"

**原因：** 数据库字符集不是 utf8mb4

**解决方案：**
```sql
ALTER DATABASE bili_monitor 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

ALTER TABLE dynamics 
CONVERT TO CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;
```

### Q3: 迁移后数据不一致

**解决方案：**

1. 清空 MySQL 数据重新迁移
```sql
TRUNCATE TABLE dynamics;
TRUNCATE TABLE upstreams;
```

2. 检查 SQLite 源数据
```bash
sqlite3 data/bili_monitor.db
SELECT COUNT(*) FROM dynamics;
```

3. 重新运行迁移脚本
```bash
python migrate_to_mysql.py
```

### Q4: 性能优化

**添加索引：**
```sql
-- 常用查询字段添加索引
ALTER TABLE dynamics ADD INDEX idx_uid_publish (uid, publish_time);
ALTER TABLE dynamics ADD INDEX idx_type (dynamic_type);
```

**优化配置：**
```yaml
# config.yaml
monitor:
  check_interval: 60    # 减少检查间隔
  retry_times: 5        # 增加重试次数
```

### Q5: 备份与恢复

**备份：**
```bash
# 使用 mysqldump
mysqldump -u bili_monitor -p bili_monitor > backup_$(date +%Y%m%d).sql

# 压缩备份
mysqldump -u bili_monitor -p bili_monitor | gzip > backup_$(date +%Y%m%d).sql.gz
```

**恢复：**
```bash
# 从备份恢复
mysql -u bili_monitor -p bili_monitor < backup_20240101.sql

# 从压缩备份恢复
gunzip < backup_20240101.sql.gz | mysql -u bili_monitor -p bili_monitor
```

---

## 📊 数据库表结构

### dynamics 表

```sql
CREATE TABLE dynamics (
    id INT AUTO_INCREMENT PRIMARY KEY,
    dynamic_id VARCHAR(64) UNIQUE NOT NULL,  -- 动态 ID
    uid VARCHAR(32) NOT NULL,                 -- UP 主 UID
    upstream_name VARCHAR(128),               -- UP 主名称
    dynamic_type VARCHAR(64),                 -- 动态类型
    content TEXT,                             -- 内容文本
    publish_time DATETIME,                    -- 发布时间
    create_time DATETIME,                     -- 创建时间
    images JSON,                              -- 图片列表 (JSON)
    video JSON,                               -- 视频信息 (JSON)
    stat_like INT DEFAULT 0,                  -- 点赞数
    stat_repost INT DEFAULT 0,                -- 转发数
    stat_comment INT DEFAULT 0,               -- 评论数
    raw_json JSON,                            -- 原始 JSON
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_uid (uid),
    INDEX idx_publish_time (publish_time),
    INDEX idx_dynamic_id (dynamic_id)
);
```

### upstreams 表

```sql
CREATE TABLE upstreams (
    id INT AUTO_INCREMENT PRIMARY KEY,
    uid VARCHAR(32) UNIQUE NOT NULL,          -- UP 主 UID
    name VARCHAR(128),                        -- UP 主名称
    face VARCHAR(512),                        -- 头像 URL
    sign TEXT,                                -- 签名
    level INT DEFAULT 0,                      -- 等级
    fans INT DEFAULT 0,                       -- 粉丝数
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🎓 最佳实践

### 1. 生产环境配置

```yaml
database:
  type: mysql
  host: 192.168.1.100      # 独立的 MySQL 服务器
  port: 3306
  user: bili_monitor
  password: strong_password
  database: bili_monitor

monitor:
  check_interval: 60       # 更频繁的检查
  retry_times: 5           # 更多重试次数
```

### 2. 监控与告警

```sql
-- 创建监控视图
CREATE VIEW v_daily_dynamics AS
SELECT 
    DATE(publish_time) as date,
    COUNT(*) as count
FROM dynamics
GROUP BY DATE(publish_time)
ORDER BY date DESC;

-- 查询每日动态数量
SELECT * FROM v_daily_dynamics LIMIT 30;
```

### 3. 定期清理

```sql
-- 清理 90 天前的数据
DELETE FROM dynamics 
WHERE publish_time < DATE_SUB(NOW(), INTERVAL 90 DAY);

-- 优化表
OPTIMIZE TABLE dynamics;
OPTIMIZE TABLE upstreams;
```

### 4. 性能调优

```sql
-- 分析慢查询
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;

-- 查看索引使用情况
EXPLAIN SELECT * FROM dynamics WHERE uid = '123456' ORDER BY publish_time DESC;
```

---

## 📞 获取帮助

遇到问题？

1. 查看日志文件：`logs/bili-monitor.log`
2. 检查 MySQL 错误日志
3. 运行测试连接：
```bash
python -c "import pymysql; pymysql.connect(host='localhost', user='root', password='your_password')"
```

---

**祝你使用愉快！** 🎉
