# MySQL 快速参考卡片

## 🚀 快速开始（3 步）

```bash
# 1. 测试连接
python test_mysql_connection.py

# 2. 初始化数据库
python init_mysql.py

# 3. 迁移数据（从 SQLite）
python migrate_to_mysql.py
```

---

## 📝 配置示例

### config.yaml

```yaml
database:
  type: mysql
  host: localhost
  port: 3306
  user: root
  password: your_password
  database: bili_monitor
```

---

## 🔧 常用命令

### 数据库操作

```bash
# 测试连接
python test_mysql_connection.py

# 初始化
python init_mysql.py

# 迁移数据
python migrate_to_mysql.py

# 启动监控
python main.py

# 查看数据
python view_dynamics.py list
```

### MySQL 命令

```bash
# 登录 MySQL
mysql -u root -p bili_monitor

# 查看表
SHOW TABLES;

# 查看数据量
SELECT COUNT(*) FROM dynamics;
SELECT COUNT(*) FROM upstreams;

# 查看最新动态
SELECT dynamic_id, upstream_name, publish_time 
FROM dynamics 
ORDER BY publish_time DESC 
LIMIT 10;

# 备份
mysqldump -u root -p bili_monitor > backup.sql

# 恢复
mysql -u root -p bili_monitor < backup.sql
```

---

## 📦 表结构

### dynamics（动态表）

| 字段 | 类型 | 说明 |
|------|------|------|
| dynamic_id | VARCHAR(64) | 动态 ID（主键） |
| uid | VARCHAR(32) | UP 主 UID |
| upstream_name | VARCHAR(128) | UP 主名称 |
| dynamic_type | VARCHAR(64) | 动态类型 |
| content | TEXT | 内容 |
| publish_time | DATETIME | 发布时间 |
| images | JSON | 图片列表 |
| video | JSON | 视频信息 |
| stat_like | INT | 点赞数 |
| stat_repost | INT | 转发数 |
| stat_comment | INT | 评论数 |

### upstreams（UP 主表）

| 字段 | 类型 | 说明 |
|------|------|------|
| uid | VARCHAR(32) | UP 主 UID（主键） |
| name | VARCHAR(128) | UP 主名称 |
| face | VARCHAR(512) | 头像 URL |
| sign | TEXT | 签名 |
| level | INT | 等级 |
| fans | INT | 粉丝数 |

---

## 🐛 故障排查

### 连接失败

```bash
# 检查 MySQL 服务
net start MySQL80  # Windows
sudo systemctl status mysql  # Linux

# 检查防火墙
sudo ufw allow 3306/tcp  # Linux
```

### 权限错误

```sql
-- 重置密码
ALTER USER 'root'@'localhost' IDENTIFIED BY 'new_password';

-- 创建用户
CREATE USER 'bili_monitor'@'%' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON bili_monitor.* TO 'bili_monitor'@'%';
FLUSH PRIVILEGES;
```

### 字符集问题

```sql
ALTER DATABASE bili_monitor CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
ALTER TABLE dynamics CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

---

## 📊 性能优化

### 索引

```sql
-- 添加复合索引
ALTER TABLE dynamics ADD INDEX idx_uid_publish (uid, publish_time DESC);

-- 查看索引
SHOW INDEX FROM dynamics;
```

### 清理旧数据

```sql
-- 删除 90 天前的数据
DELETE FROM dynamics WHERE publish_time < DATE_SUB(NOW(), INTERVAL 90 DAY);

-- 优化表
OPTIMIZE TABLE dynamics;
OPTIMIZE TABLE upstreams;
```

---

## 📚 文档链接

- [MYSQL_SETUP.md](MYSQL_SETUP.md) - 详细配置指南
- [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md) - 迁移指南
- [MYSQL_MIGRATION_SUMMARY.md](MYSQL_MIGRATION_SUMMARY.md) - 总结文档
- [README.md](README.md) - 项目说明

---

## 💡 提示

- ✅ 生产环境使用 MySQL，开发环境使用 SQLite
- ✅ 定期备份数据库（建议每日）
- ✅ 监控磁盘空间和数据库大小
- ✅ 使用强密码保护数据库
- ✅ 启用慢查询日志优化性能

---

**快速参考卡片 - 打印保存！** 📋
