# SQLite 到 MySQL 完整转换指南

## 📊 当前状态

✅ **已完成的工作：**
- 项目代码已支持 MySQL
- 配置文件已创建（config.yaml）
- 测试工具已就绪
- SQLite 数据库为空（无需迁移数据）

⚠️ **待完成的工作：**
- 安装并启动 MySQL 服务
- 初始化 MySQL 数据库
- 验证连接

---

## 🚀 方案选择（3 种方式）

### 方案 1: Docker（推荐，最简单）⭐

**优势：**
- ✅ 一键安装，无需配置
- ✅ 环境隔离，不影响系统
- ✅ 易于管理和删除

**步骤：**

#### 1. 启动 Docker Desktop
```powershell
# 在 Windows 开始菜单搜索 "Docker Desktop" 并启动
# 或运行：
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"
```

等待 Docker Desktop 启动完成（托盘图标变为绿色）。

#### 2. 运行 MySQL 容器
```powershell
docker run -d `
  --name mysql-bili `
  -e MYSQL_ROOT_PASSWORD=bili_monitor_2024 `
  -e MYSQL_DATABASE=bili_monitor `
  -p 3306:3306 `
  mysql:8.0
```

#### 3. 等待 MySQL 启动（约 30 秒）
```powershell
# 查看日志
docker logs mysql-bili

# 看到 "ready for connections" 表示启动成功
```

#### 4. 更新配置文件
编辑 `config.yaml`：
```yaml
database:
  type: mysql
  host: localhost
  port: 3306
  user: root
  password: bili_monitor_2024
  database: bili_monitor
```

---

### 方案 2: MySQL Installer（适合生产环境）

**优势：**
- ✅ 完整的 MySQL 功能
- ✅ 图形化管理工具
- ✅ 性能最优

**步骤：**

#### 1. 下载 MySQL Installer
```
https://dev.mysql.com/downloads/installer/
```
选择 "mysql-installer-community-8.0.xx.msi"

#### 2. 安装 MySQL Server
- 运行安装程序
- 选择 "Server only" 或 "Full"
- 设置 root 密码（记住这个密码）
- 默认端口：3306

#### 3. 启动 MySQL 服务
```powershell
# 检查服务状态
Get-Service MySQL*

# 启动服务
net start MySQL80
```

#### 4. 更新配置文件
编辑 `config.yaml`：
```yaml
database:
  type: mysql
  host: localhost
  port: 3306
  user: root
  password: 你的密码
  database: bili_monitor
```

---

### 方案 3: XAMPP（适合开发测试）

**优势：**
- ✅ 包含 MySQL + Apache + PHP
- ✅ 图形化管理工具
- ✅ 安装简单

**步骤：**

#### 1. 下载 XAMPP
```
https://www.apachefriends.org/
```

#### 2. 安装并启动
- 运行 XAMPP 安装程序
- 打开 XAMPP Control Panel
- 点击 MySQL 的 "Start" 按钮

#### 3. 更新配置文件
编辑 `config.yaml`：
```yaml
database:
  type: mysql
  host: localhost
  port: 3306
  user: root
  password: ""        # XAMPP 默认无密码
  database: bili_monitor
```

---

## ✅ 完成转换（3 步）

### 步骤 1: 测试 MySQL 连接

选择上述任一方案安装 MySQL 后，运行：

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

### 步骤 2: 初始化数据库

```powershell
python init_mysql.py
```

**预期输出：**
```
============================================================
MySQL 数据库初始化工具
============================================================

✅ 配置文件加载成功
✅ 数据库 bili_monitor 已存在
✅ MySQL 数据库连接成功：localhost:3306/bili_monitor
✅ 表 dynamics 创建成功
✅ 表 upstreams 创建成功
✅ 表 state 创建成功

============================================================
✅ MySQL 数据库初始化完成！
============================================================
```

### 步骤 3: 启动监控程序

```powershell
python main.py
```

---

## 🔄 数据迁移（如果有旧数据）

如果你有 SQLite 数据库文件（`data/bili_monitor.db`），可以迁移到 MySQL：

```powershell
# 1. 确保 MySQL 服务运行
python test_mysql_standalone.py

# 2. 运行迁移脚本
python migrate_to_mysql.py

# 3. 验证迁移结果
python view_dynamics.py list
```

---

## 🐛 故障排查

### 问题 1: Docker Desktop 未运行

**错误：** `error during connect: open //./pipe/dockerDesktopLinuxEngine`

**解决方案：**
```powershell
# 启动 Docker Desktop
Start-Process "C:\Program Files\Docker\Docker\Docker Desktop.exe"

# 等待 30 秒后重试
```

### 问题 2: MySQL 服务未启动

**错误：** `Can't connect to MySQL server on 'localhost'`

**解决方案：**
```powershell
# 检查 MySQL 服务
Get-Service MySQL*

# 启动服务
net start MySQL80

# 或使用 Docker
docker start mysql-bili
```

### 问题 3: 密码错误

**错误：** `Access denied for user 'root'@'localhost'`

**解决方案：**
检查 `config.yaml` 中的密码是否正确：
- Docker: `password: bili_monitor_2024`
- MySQL Installer: 你设置的密码
- XAMPP: `password: ""`（空密码）

---

## 📊 对比：SQLite vs MySQL

| 特性 | SQLite | MySQL | 提升 |
|------|--------|-------|------|
| **并发性能** | 文件级锁 | 行级锁 | ⬆️ 100x+ |
| **数据量支持** | < 10GB | 无限制 | ⬆️ 无限 |
| **多用户访问** | ❌ 不支持 | ✅ 支持 | ✅ |
| **网络访问** | ❌ 本地 | ✅ 远程 | ✅ |
| **备份恢复** | 文件复制 | 在线热备 | ⬆️ 高效 |
| **适用场景** | 开发/测试 | 生产环境 | ✅ |

---

## 🎯 推荐方案

根据你的情况：

| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| **快速开始** | Docker | 你已安装 Docker，最简单 |
| **生产环境** | MySQL Installer | 性能最优，完全控制 |
| **开发测试** | XAMPP | 图形化管理，简单易用 |

---

## 📝 快速命令参考

```powershell
# Docker 方案
docker run -d --name mysql-bili -e MYSQL_ROOT_PASSWORD=bili_monitor_2024 -e MYSQL_DATABASE=bili_monitor -p 3306:3306 mysql:8.0
docker logs mysql-bili
docker start mysql-bili
docker stop mysql-bili

# 测试连接
python test_mysql_standalone.py

# 初始化数据库
python init_mysql.py

# 启动监控
python main.py

# 查看数据
python view_dynamics.py list
```

---

## 📞 需要帮助？

如果遇到问题：

1. 查看 [MYSQL_INSTALL_GUIDE.md](MYSQL_INSTALL_GUIDE.md) - 详细安装指南
2. 查看 [MYSQL_QUICK_REFERENCE.md](MYSQL_QUICK_REFERENCE.md) - 快速参考
3. 检查日志文件：`logs/bili-monitor.log`

---

**选择适合你的方案，开始转换吧！** 🚀

**推荐：** 使用 Docker 方案（你已安装 Docker Desktop），只需启动 Docker Desktop 然后运行一条命令即可。
