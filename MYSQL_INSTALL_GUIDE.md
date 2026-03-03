# MySQL 安装与配置快速指南

## 🎯 当前状态

✅ 项目代码已支持 MySQL  
✅ 配置文件已创建（config.yaml）  
✅ 测试工具已就绪  
⚠️  MySQL 服务未启动或未安装  

---

## 📦 MySQL 安装选项

### 方案 1: Docker（推荐，最简单）

**优势：**
- ✅ 一键安装，无需配置
- ✅ 环境隔离，不影响系统
- ✅ 易于管理和删除

**安装步骤：**

```powershell
# 1. 安装 Docker Desktop（如果没有）
# 下载：https://www.docker.com/products/docker-desktop

# 2. 启动 MySQL 容器
docker run -d `
  --name mysql-bili `
  -e MYSQL_ROOT_PASSWORD=your_password `
  -e MYSQL_DATABASE=bili_monitor `
  -p 3306:3306 `
  mysql:8.0

# 3. 验证运行状态
docker ps | findstr mysql

# 4. 查看日志
docker logs mysql-bili
```

**管理命令：**

```powershell
# 停止容器
docker stop mysql-bili

# 启动容器
docker start mysql-bili

# 删除容器
docker rm -f mysql-bili

# 进入 MySQL 命令行
docker exec -it mysql-bili mysql -u root -p
```

---

### 方案 2: Windows 本地安装

**安装步骤：**

1. **下载 MySQL Installer**
   ```
   https://dev.mysql.com/downloads/installer/
   ```

2. **安装 MySQL Server**
   - 选择 "Server only" 或 "Full"
   - 设置 root 密码（记住这个密码）
   - 默认端口：3306

3. **启动 MySQL 服务**
   ```powershell
   # 检查服务状态
   Get-Service MySQL*
   
   # 启动服务
   net start MySQL80
   
   # 或通过服务管理器
   services.msc
   ```

4. **验证安装**
   ```powershell
   # 登录 MySQL
   mysql -u root -p
   
   # 查看版本
   SELECT VERSION();
   ```

---

### 方案 3: 使用 XAMPP/WAMP（适合开发）

**优势：**
- ✅ 包含 MySQL + Apache + PHP
- ✅ 图形化管理工具
- ✅ 适合本地开发

**安装步骤：**

1. **下载 XAMPP**
   ```
   https://www.apachefriends.org/
   ```

2. **安装并启动**
   - 运行 XAMPP Control Panel
   - 启动 MySQL 服务
   - 默认用户名：root，密码：空

3. **修改配置**
   ```yaml
   # config.yaml
   database:
     type: mysql
     host: localhost
     port: 3306
     user: root
     password: ""        # XAMPP 默认无密码
     database: bili_monitor
   ```

---

## 🔧 配置 MySQL

### 1. 创建数据库

**方式 A: 使用初始化脚本（推荐）**

```powershell
# 先启动 MySQL 服务，然后运行
python init_mysql.py
```

**方式 B: 手动创建**

```powershell
# 登录 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE bili_monitor 
DEFAULT CHARACTER SET utf8mb4 
DEFAULT COLLATE utf8mb4_unicode_ci;

# 创建用户（可选）
CREATE USER 'bili_monitor'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON bili_monitor.* TO 'bili_monitor'@'localhost';
FLUSH PRIVILEGES;

# 退出
EXIT;
```

### 2. 修改配置文件

编辑 `config.yaml`：

```yaml
database:
  type: mysql
  host: localhost
  port: 3306
  user: root
  password: your_password    # 改为你的密码
  database: bili_monitor
```

---

## ✅ 验证安装

### 1. 测试连接

```powershell
python test_mysql_standalone.py
```

**预期输出：**
```
✅ pymysql 已安装
✅ pyyaml 已安装
============================================================
MySQL 连接测试（独立版）
============================================================

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

### 2. 初始化数据库

```powershell
python init_mysql.py
```

### 3. 测试完整功能

```powershell
# 安装所有依赖
pip install requests tenacity fastapi uvicorn qrcode pillow

# 启动监控（测试数据库连接）
python main.py
```

---

## 🐛 常见问题

### Q1: 连接被拒绝

**错误：** `Can't connect to MySQL server on 'localhost'`

**解决方案：**

```powershell
# 1. 检查 MySQL 服务是否运行
Get-Service MySQL*

# 2. 启动服务
net start MySQL80

# 3. 如果是 Docker
docker start mysql-bili

# 4. 检查端口占用
netstat -ano | findstr :3306
```

### Q2: 密码错误

**错误：** `Access denied for user 'root'@'localhost'`

**解决方案：**

```powershell
# 1. 确认密码正确
# 2. 如果忘记密码，重置密码：

# 停止 MySQL 服务
net stop MySQL80

# 跳过权限启动
mysqld --skip-grant-tables

# 新开终端，无密码登录
mysql -u root

# 重置密码
USE mysql;
UPDATE user SET authentication_string=PASSWORD('new_password') WHERE User='root';
FLUSH PRIVILEGES;
EXIT;

# 重启 MySQL 服务
net start MySQL80
```

### Q3: 字符集问题

**错误：** `Incorrect string value`

**解决方案：**

```sql
-- 登录 MySQL
mysql -u root -p

-- 修改数据库字符集
ALTER DATABASE bili_monitor 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;
```

---

## 📊 性能优化（可选）

### 1. 修改 MySQL 配置

**编辑配置文件：**
```
C:\ProgramData\MySQL\MySQL Server 8.0\my.ini
```

**添加配置：**
```ini
[mysqld]
# 字符集
character-set-server = utf8mb4
collation-server = utf8mb4_unicode_ci

# 内存配置（根据你的内存调整）
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M

# 连接数
max_connections = 200

# 查询缓存
query_cache_size = 64M
query_cache_type = 1
```

**重启服务：**
```powershell
net stop MySQL80
net start MySQL80
```

### 2. 创建索引

```sql
-- 登录 MySQL
mysql -u root -p bili_monitor

-- 添加索引
ALTER TABLE dynamics ADD INDEX idx_uid_publish (uid, publish_time DESC);
ALTER TABLE dynamics ADD INDEX idx_type (dynamic_type);

-- 查看索引
SHOW INDEX FROM dynamics;
```

---

## 🎓 推荐方案

根据你的使用场景选择：

| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| **快速测试** | Docker | 一键启动，无需配置 |
| **本地开发** | XAMPP | 图形化管理，简单易用 |
| **生产环境** | 独立安装 | 性能最优，完全控制 |
| **学习 MySQL** | 独立安装 | 完整体验所有功能 |

---

## 📝 下一步

1. ✅ 选择一种方案安装 MySQL
2. ✅ 启动 MySQL 服务
3. ✅ 修改 config.yaml 中的密码
4. ✅ 运行 `python test_mysql_standalone.py` 测试连接
5. ✅ 运行 `python init_mysql.py` 初始化数据库
6. ✅ 运行 `python main.py` 启动监控

---

## 📞 获取帮助

如果遇到问题：

1. 查看错误日志
2. 检查 MySQL 服务状态
3. 验证配置文件
4. 查看详细文档：
   - [MYSQL_SETUP.md](MYSQL_SETUP.md)
   - [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)
   - [MYSQL_QUICK_REFERENCE.md](MYSQL_QUICK_REFERENCE.md)

---

**选择适合你的方案，开始使用 MySQL 吧！** 🚀
