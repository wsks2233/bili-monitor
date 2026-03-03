# Docker 部署指南

## 🎯 部署方案说明

### 架构优势

本项目采用 **Docker Compose** 部署，解决了你担心的问题：

✅ **统一部署** - 应用和数据库在同一个 Docker Compose 中  
✅ **自动连接** - 应用自动连接到 MySQL 容器  
✅ **数据持久化** - MySQL 数据存储在 Docker Volume 中  
✅ **一键启动** - 只需一条命令启动整个系统  

---

## 📊 部署架构

```
Docker Compose
├── bili-monitor (应用容器)
│   ├── FastAPI Web 服务
│   ├── 监控程序
│   └── 自动连接到 MySQL
│
└── mysql (数据库容器)
    ├── MySQL 8.0
    ├── 数据持久化 (Volume)
    └── 自动健康检查
```

---

## 🚀 快速开始

### 方式 1: Docker Compose（推荐）

#### 1. 一键启动

```powershell
# 启动所有服务（应用 + MySQL）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 查看服务状态
docker-compose ps
```

#### 2. 访问应用

```
Web 界面: http://localhost:8000
API 文档: http://localhost:8000/docs
```

#### 3. 管理命令

```powershell
# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 查看应用日志
docker-compose logs -f bili-monitor

# 查看 MySQL 日志
docker-compose logs -f mysql

# 进入 MySQL 命令行
docker-compose exec mysql mysql -u root -pbili_monitor_2024 bili_monitor
```

---

### 方式 2: 仅启动应用（使用外部 MySQL）

如果你有外部的 MySQL 服务：

#### 1. 修改配置

编辑 `config.yaml`：

```yaml
database:
  type: mysql
  host: your-mysql-host  # 外部 MySQL 地址
  port: 3306
  user: root
  password: your_password
  database: bili_monitor
```

#### 2. 仅启动应用

```powershell
# 仅启动应用容器
docker-compose up -d bili-monitor
```

---

## 🔧 配置说明

### Docker 环境 vs 本地环境

| 环境 | 配置文件 | MySQL 地址 | 说明 |
|------|---------|-----------|------|
| **本地开发** | `config.yaml` | `localhost:3306` | 本地 MySQL 或 Docker MySQL |
| **Docker 部署** | `config.docker.yaml` | `mysql:3306` | Docker Compose 服务名 |

### 配置文件优先级

1. **Docker 部署时**：自动使用 `config.docker.yaml`
2. **本地运行时**：使用 `config.yaml`

---

## 📦 数据持久化

### Volume 说明

```yaml
volumes:
  mysql_data:          # MySQL 数据持久化
    driver: local
  
  ./data:              # SQLite 数据（如果使用）
  ./logs:              # 应用日志
  ./images:            # 下载的图片
```

### 备份数据

```powershell
# 备份 MySQL 数据
docker-compose exec mysql mysqldump -u root -pbili_monitor_2024 bili_monitor > backup.sql

# 备份所有数据（包括图片、日志）
tar -czf backup.tar.gz data logs images
```

### 恢复数据

```powershell
# 恢复 MySQL 数据
docker-compose exec -T mysql mysql -u root -pbili_monitor_2024 bili_monitor < backup.sql

# 恢复文件数据
tar -xzf backup.tar.gz
```

---

## 🌐 生产环境部署

### 1. 环境变量配置

创建 `.env` 文件：

```env
# MySQL 配置
MYSQL_ROOT_PASSWORD=your_strong_password
MYSQL_DATABASE=bili_monitor

# 应用配置
MONITOR_CHECK_INTERVAL=300
TZ=Asia/Shanghai
```

更新 `docker-compose.yml`：

```yaml
services:
  mysql:
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD}
      - MYSQL_DATABASE=${MYSQL_DATABASE}
```

### 2. 安全配置

```yaml
services:
  bili-monitor:
    environment:
      - TZ=Asia/Shanghai
    # 不暴露 MySQL 端口到宿主机
    # ports:
    #   - "3306:3306"  # 注释掉
```

### 3. 资源限制

```yaml
services:
  bili-monitor:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

### 4. 反向代理（Nginx）

```yaml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - bili-monitor
```

---

## 🔄 更新部署

### 更新应用

```powershell
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f bili-monitor
```

### 更新 MySQL

```powershell
# 停止服务
docker-compose down

# 备份数据
docker-compose exec mysql mysqldump -u root -pbili_monitor_2024 bili_monitor > backup.sql

# 更新 MySQL 版本
# 修改 docker-compose.yml 中的 MySQL 版本

# 重新启动
docker-compose up -d
```

---

## 🐛 故障排查

### 问题 1: MySQL 连接失败

**错误：** `Can't connect to MySQL server on 'mysql'`

**解决方案：**

```powershell
# 检查 MySQL 容器状态
docker-compose ps mysql

# 查看 MySQL 日志
docker-compose logs mysql

# 检查网络连接
docker-compose exec bili-monitor ping mysql
```

### 问题 2: 应用启动失败

**解决方案：**

```powershell
# 查看应用日志
docker-compose logs bili-monitor

# 进入容器调试
docker-compose exec bili-monitor bash

# 手动测试连接
docker-compose exec bili-monitor python test_mysql_standalone.py
```

### 问题 3: 数据丢失

**解决方案：**

```powershell
# 检查 Volume
docker volume ls

# 查看 Volume 详情
docker volume inspect bili-monitor_mysql_data

# 恢复数据
docker-compose exec -T mysql mysql -u root -pbili_monitor_2024 bili_monitor < backup.sql
```

---

## 📊 性能优化

### 1. MySQL 配置优化

创建 `mysql.cnf`：

```ini
[mysqld]
innodb_buffer_pool_size = 1G
innodb_log_file_size = 256M
max_connections = 200
query_cache_size = 64M
```

挂载到容器：

```yaml
services:
  mysql:
    volumes:
      - ./mysql.cnf:/etc/mysql/conf.d/custom.cnf
```

### 2. 应用优化

```yaml
services:
  bili-monitor:
    environment:
      - MONITOR_CHECK_INTERVAL=60  # 更频繁的检查
    deploy:
      resources:
        limits:
          memory: 512M
```

---

## 🎓 最佳实践

### 1. 开发环境

```powershell
# 使用本地配置
python main.py

# 或使用 Docker（包含 MySQL）
docker-compose up -d
```

### 2. 生产环境

```powershell
# 使用环境变量
cp .env.example .env
# 编辑 .env 设置密码

# 启动服务
docker-compose up -d

# 设置自动重启
docker-compose restart
```

### 3. CI/CD 集成

```yaml
# .github/workflows/deploy.yml
- name: Deploy to production
  run: |
    docker-compose pull
    docker-compose up -d
    docker-compose exec -T mysql mysql -u root -p${MYSQL_ROOT_PASSWORD} -e "SELECT 1"
```

---

## 📝 快速命令参考

```powershell
# 启动所有服务
docker-compose up -d

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 停止服务
docker-compose down

# 进入应用容器
docker-compose exec bili-monitor bash

# 进入 MySQL
docker-compose exec mysql mysql -u root -pbili_monitor_2024 bili_monitor

# 备份数据库
docker-compose exec mysql mysqldump -u root -pbili_monitor_2024 bili_monitor > backup.sql

# 查看容器状态
docker-compose ps

# 查看资源使用
docker stats
```

---

## 🌟 总结

### 优势

✅ **一键部署** - `docker-compose up -d` 启动所有服务  
✅ **自动连接** - 应用自动连接到 MySQL 容器  
✅ **数据持久化** - Volume 保证数据不丢失  
✅ **易于扩展** - 可以轻松添加 Redis、Nginx 等服务  
✅ **环境一致** - 开发和生产环境完全一致  

### 架构对比

| 方案 | 本地开发 | Docker 部署 | 说明 |
|------|---------|------------|------|
| **MySQL** | Docker 或本地 | Docker Compose | 统一管理 |
| **应用** | Python 直接运行 | Docker 容器 | 环境一致 |
| **配置** | config.yaml | config.docker.yaml | 自动切换 |
| **数据** | 本地文件 | Docker Volume | 持久化 |

---

**现在你可以放心使用 Docker 部署，不会再有重复安装 MySQL 的问题！** 🎉
