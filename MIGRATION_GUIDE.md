# MySQL 迁移指南

## 📋 迁移概览

本项目已完全支持 MySQL 数据库存储。本文档提供从 SQLite 迁移到 MySQL 的完整解决方案。

---

## 🎯 迁移优势

### 为什么选择 MySQL？

| 对比项 | SQLite | MySQL | 提升 |
|--------|--------|-------|------|
| **并发性能** | 文件级锁 | 行级锁 | ⬆️ 100x+ |
| **数据量支持** | < 10GB | 无限制 | ⬆️ 无限 |
| **多用户访问** | ❌ 不支持 | ✅ 支持 | ✅ |
| **网络访问** | ❌ 本地 | ✅ 远程 | ✅ |
| **备份恢复** | 文件复制 | 在线热备 | ⬆️ 高效 |
| **监控工具** | 有限 | 丰富 | ✅ |

### 适用场景

- ✅ **生产环境**: 需要 7x24 小时稳定运行
- ✅ **多实例部署**: 多个监控节点共享数据
- ✅ **大数据量**: 监控大量 UP 主，存储数百万动态
- ✅ **高并发**: 频繁的读写操作
- ✅ **数据备份**: 需要定期备份和恢复

---

## 🚀 快速开始（3 步迁移）

### 步骤 1: 准备 MySQL 环境

```bash
# 安装 MySQL（选择一种方式）

# 方式 1: Docker（推荐）
docker run -d \
  --name mysql-bili \
  -e MYSQL_ROOT_PASSWORD=your_password \
  -e MYSQL_DATABASE=bili_monitor \
  -p 3306:3306 \
  mysql:8.0

# 方式 2: Ubuntu/Debian
sudo apt install mysql-server
sudo systemctl start mysql

# 方式 3: Windows
# 下载 MySQL Installer: https://dev.mysql.com/downloads/installer/
```

### 步骤 2: 配置并初始化

```bash
# 1. 编辑 config.yaml
# 修改 database 部分为 MySQL 配置

# 2. 测试连接
python test_mysql_connection.py

# 3. 初始化数据库
python init_mysql.py
```

### 步骤 3: 迁移数据

```bash
# 迁移 SQLite 数据到 MySQL
python migrate_to_mysql.py

# 验证迁移结果
python view_dynamics.py list
```

---

## 📦 详细迁移步骤

### 1. 安装依赖

```bash
pip install pymysql
```

### 2. 配置 MySQL

编辑 `config.yaml`:

```yaml
database:
  type: mysql
  host: localhost          # MySQL 服务器地址
  port: 3306              # 端口
  user: root              # 用户名
  password: your_password # 密码
  database: bili_monitor  # 数据库名
```

### 3. 创建数据库

**方式 A: 使用初始化脚本（推荐）**

```bash
python init_mysql.py
```

**方式 B: 手动创建**

```sql
CREATE DATABASE bili_monitor 
DEFAULT CHARACTER SET utf8mb4 
DEFAULT COLLATE utf8mb4_unicode_ci;

CREATE USER 'bili_monitor'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON bili_monitor.* TO 'bili_monitor'@'%';
FLUSH PRIVILEGES;
```

### 4. 测试连接

```bash
python test_mysql_connection.py
```

**预期输出：**
```
✅ 配置文件加载成功

📋 连接信息:
  主机：localhost:3306
  用户：root
  数据库：bili_monitor

🔌 正在连接 MySQL...
✅ MySQL 连接成功！

📊 数据库信息:
  MySQL 版本：8.0.35
  字符集：utf8mb4
  排序规则：utf8mb4_unicode_ci

📁 现有表:
  (空数据库，需要运行 init_mysql.py 初始化)

============================================================
✅ MySQL 连接测试通过！
============================================================
```

### 5. 初始化表结构

```bash
python init_mysql.py
```

**输出示例：**
```
✅ 数据库 bili_monitor 创建成功
✅ MySQL 数据库连接成功：localhost:3306/bili_monitor
✅ 表 dynamics 创建成功
✅ 表 upstreams 创建成功
✅ 表 state 创建成功

============================================================
✅ MySQL 数据库初始化完成！
============================================================
```

### 6. 迁移数据

```bash
python migrate_to_mysql.py
```

**输出示例：**
```
============================================================
SQLite 到 MySQL 数据迁移工具
============================================================

✅ 配置文件加载成功
✅ SQLite 数据库连接成功：data/bili_monitor.db
✅ MySQL 数据库连接成功：localhost:3306/bili_monitor

============================================================
开始迁移数据
============================================================

📦 开始迁移表 dynamics，共 1523 条记录
✅ 表 dynamics 迁移完成，成功 1523/1523 条
📦 开始迁移表 upstreams，共 15 条记录
✅ 表 upstreams 迁移完成，成功 15/15 条

============================================================
验证迁移结果
============================================================
✅ 表 dynamics: SQLite=1523, MySQL=1523
✅ 表 upstreams: SQLite=15, MySQL=15

============================================================
✅ 数据迁移完成！
============================================================
```

### 7. 验证与切换

```bash
# 查看 MySQL 中的数据
python view_dynamics.py list

# 或使用 MySQL 客户端
mysql -u root -p bili_monitor
SELECT COUNT(*) FROM dynamics;
SELECT COUNT(*) FROM upstreams;
```

---

## 🔧 故障排查

### 问题 1: 连接失败

**错误信息：**
```
❌ 连接失败：Can't connect to MySQL server
```

**解决方案：**

1. 检查 MySQL 服务状态
```bash
# Windows
net start MySQL80

# Linux
sudo systemctl status mysql

# Docker
docker ps | grep mysql
```

2. 检查防火墙
```bash
# Linux
sudo ufw allow 3306/tcp

# Windows
# 控制面板 -> Windows Defender 防火墙 -> 高级设置
# 添加入站规则，允许 TCP 3306
```

3. 检查绑定地址
```bash
# 编辑 MySQL 配置文件
# Linux: /etc/mysql/mysql.conf.d/mysqld.cnf
# Windows: C:\ProgramData\MySQL\MySQL Server 8.0\my.ini

# 修改或添加
bind-address = 0.0.0.0

# 重启 MySQL
sudo systemctl restart mysql
```

### 问题 2: 权限错误

**错误信息：**
```
❌ 访问被拒绝：Access denied for user 'root'@'localhost'
```

**解决方案：**

```sql
-- 登录 MySQL
mysql -u root -p

-- 重置密码
ALTER USER 'root'@'localhost' IDENTIFIED BY 'new_password';
FLUSH PRIVILEGES;

-- 创建专用用户
CREATE USER 'bili_monitor'@'%' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON bili_monitor.* TO 'bili_monitor'@'%';
FLUSH PRIVILEGES;
```

### 问题 3: 字符集错误

**错误信息：**
```
Incorrect string value: '\xF0\x9F...' for column
```

**解决方案：**

```sql
-- 修改数据库字符集
ALTER DATABASE bili_monitor 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 修改表字符集
ALTER TABLE dynamics 
CONVERT TO CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

ALTER TABLE upstreams 
CONVERT TO CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;
```

### 问题 4: 迁移失败

**错误信息：**
```
❌ 迁移 dynamics 记录失败：Duplicate entry 'xxx' for key 'dynamic_id'
```

**解决方案：**

1. 清空 MySQL 数据重新迁移
```sql
USE bili_monitor;
TRUNCATE TABLE dynamics;
TRUNCATE TABLE upstreams;
```

2. 重新运行迁移
```bash
python migrate_to_mysql.py
```

---

## 📊 性能优化

### 1. 索引优化

```sql
-- 添加复合索引
ALTER TABLE dynamics 
ADD INDEX idx_uid_publish (uid, publish_time DESC);

-- 添加类型索引
ALTER TABLE dynamics 
ADD INDEX idx_type (dynamic_type);

-- 查看索引使用情况
SHOW INDEX FROM dynamics;
```

### 2. 查询优化

```sql
-- 使用 EXPLAIN 分析查询
EXPLAIN SELECT * FROM dynamics 
WHERE uid = '123456' 
ORDER BY publish_time DESC 
LIMIT 20;

-- 优化前：全表扫描
-- type: ALL, rows: 10000

-- 优化后：使用索引
-- type: ref, rows: 50
```

### 3. 配置优化

**编辑 MySQL 配置文件：**

```ini
[mysqld]
# 内存配置
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M

# 连接数
max_connections = 200

# 查询缓存（MySQL 5.7）
query_cache_size = 64M
query_cache_type = 1

# 字符集
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci
```

### 4. 定期维护

```sql
-- 分析表
ANALYZE TABLE dynamics;
ANALYZE TABLE upstreams;

-- 优化表
OPTIMIZE TABLE dynamics;
OPTIMIZE TABLE upstreams;

-- 检查表
CHECK TABLE dynamics;
CHECK TABLE upstreams;
```

---

## 🔄 备份与恢复

### 备份

```bash
# 完整备份
mysqldump -u bili_monitor -p \
  --single-transaction \
  --routines \
  --triggers \
  bili_monitor > backup_$(date +%Y%m%d_%H%M%S).sql

# 压缩备份
mysqldump -u bili_monitor -p bili_monitor | gzip > backup_$(date +%Y%m%d).sql.gz

# 仅结构
mysqldump -u bili_monitor -p --no-data bili_monitor > schema.sql

# 仅数据
mysqldump -u bili_monitor -p --no-create-info bili_monitor > data.sql
```

### 恢复

```bash
# 从备份恢复
mysql -u bili_monitor -p bili_monitor < backup_20240101.sql

# 从压缩备份恢复
gunzip < backup_20240101.sql.gz | mysql -u bili_monitor -p bili_monitor

# 恢复单个表
mysql -u bili_monitor -p bili_monitor < table_backup.sql
```

### 定时备份（Cron）

```bash
# 编辑 crontab
crontab -e

# 添加每日备份任务（每天凌晨 2 点）
0 2 * * * /usr/bin/mysqldump -u bili_monitor -p'password' bili_monitor | gzip > /backup/bili_$(date +\%Y\%m\%d).sql.gz
```

---

## 📈 监控与告警

### 1. 数据库大小监控

```sql
-- 查看数据库大小
SELECT 
    table_schema AS '数据库',
    table_name AS '表',
    ROUND((data_length + index_length) / 1024 / 1024, 2) AS '大小 (MB)',
    table_rows AS '行数'
FROM information_schema.tables
WHERE table_schema = 'bili_monitor'
ORDER BY (data_length + index_length) DESC;
```

### 2. 慢查询日志

```sql
-- 启用慢查询日志
SET GLOBAL slow_query_log = 'ON';
SET GLOBAL long_query_time = 2;

-- 查看慢查询
SHOW VARIABLES LIKE 'slow_query_log_file';
```

### 3. 连接数监控

```sql
-- 查看当前连接数
SHOW STATUS LIKE 'Threads_connected';

-- 查看最大连接数
SHOW VARIABLES LIKE 'max_connections';

-- 查看连接历史
SHOW STATUS LIKE 'Threads_created';
```

---

## 🎓 最佳实践

### 1. 生产环境配置

```yaml
# config.yaml
database:
  type: mysql
  host: 192.168.1.100      # 独立数据库服务器
  port: 3306
  user: bili_monitor
  password: strong_password
  database: bili_monitor

monitor:
  check_interval: 60       # 更频繁的检查
  retry_times: 5           # 更多重试
```

### 2. 数据清理策略

```sql
-- 创建存储过程清理旧数据
DELIMITER $$
CREATE PROCEDURE cleanup_old_dynamics()
BEGIN
    DELETE FROM dynamics 
    WHERE publish_time < DATE_SUB(NOW(), INTERVAL 90 DAY);
END$$
DELIMITER ;

-- 定时执行（Event Scheduler）
SET GLOBAL event_scheduler = ON;

CREATE EVENT cleanup_event
ON SCHEDULE EVERY 1 DAY
DO CALL cleanup_old_dynamics();
```

### 3. 读写分离（高级）

```yaml
# 主库（写）
database:
  type: mysql
  host: master.db.local
  user: bili_writer
  password: write_password
  database: bili_monitor

# 从库（读）- 需要修改代码支持
read_database:
  type: mysql
  host: slave.db.local
  user: bili_reader
  password: read_password
  database: bili_monitor
```

---

## 📞 获取帮助

### 日志文件

```bash
# 应用日志
tail -f logs/bili-monitor.log

# MySQL 错误日志
# Linux: /var/log/mysql/error.log
# Windows: C:\ProgramData\MySQL\MySQL Server 8.0\Data\*.err
```

### 诊断命令

```bash
# 测试连接
python test_mysql_connection.py

# 检查配置
python -c "from bili_monitor.core.config import load_config; c = load_config(); print(c.database)"

# 查看数据库状态
mysql -u root -p -e "SHOW DATABASES; SHOW TABLES FROM bili_monitor;"
```

---

## 📚 相关文档

- [MYSQL_SETUP.md](MYSQL_SETUP.md) - 详细配置指南
- [README.md](README.md) - 项目说明
- [config.example.yaml](config.example.yaml) - 配置示例

---

**祝你迁移顺利！** 🎉

如有问题，请查看日志文件或提交 Issue。
