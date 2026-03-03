# Cookie 服务统一接口使用说明

## 概述

已将项目中所有 Cookie 相关功能（保活、状态查询、获取、扫码登录等）统一整合到 `CookieService` 类中。

## 模块结构

```
bili_monitor/api/
├── cookie_service.py    # 统一的 Cookie 服务接口（新增）
├── cookie_manager.py    # Cookie 管理器（保留，作为底层实现）
└── bili_api.py          # B 站 API 客户端
```

## 主要功能

### 1. CookieService 类

提供以下功能：
- ✅ Cookie 有效性检测
- ✅ Cookie 保活管理
- ✅ Cookie 状态查询
- ✅ Cookie 更新与持久化
- ✅ 扫码登录支持

### 2. 使用示例

#### 2.1 在 Web 服务中使用

```python
from bili_monitor.api.cookie_service import CookieService, get_cookie_service

# 获取全局 Cookie 服务实例
cookie_service = get_cookie_service(config_path="config.yaml")

# 检查 Cookie 状态
status = cookie_service.check_status()
print(f"Cookie 有效：{status.is_valid}")
print(f"用户名：{status.username}")
print(f"剩余天数：{status.remaining_days}")

# 启动保活
cookie_service.start_keepalive()

# 扫码登录
qrcode_url, qrcode_key = cookie_service.get_qrcode()
# 用户扫码后检查状态
login_status = cookie_service.check_login(qrcode_key)
if login_status.success:
    print(f"登录成功，用户：{login_status.username}")
    # Cookie 已自动保存到配置文件
```

#### 2.2 在监控服务中使用

```python
from bili_monitor.api.cookie_service import CookieService

# 创建 Cookie 服务
cookie_service = CookieService(
    cookie=config.monitor.cookie,
    config_path="config.yaml",
    logger=logger
)

# 检查状态
status = cookie_service.check_status()
if status.is_valid:
    # 启动保活
    cookie_service.start_keepalive()
    
    # 设置过期回调
    def on_expired(status):
        logger.error(f"Cookie 已过期：{status.message}")
    
    cookie_service.on_cookie_expired = on_expired
```

#### 2.3 独立的 Cookie 状态检查

```python
from bili_monitor.api.cookie_service import check_cookie_status_standalone

# 快速检查 Cookie 状态（无需创建服务实例）
result = check_cookie_status_standalone(cookie_string)
print(f"有效：{result['valid']}")
print(f"用户名：{result['username']}")
```

## API 接口

### CookieService 方法

| 方法 | 说明 | 返回值 |
|------|------|--------|
| `check_status()` | 检查 Cookie 状态 | `ServiceStatus` |
| `start_keepalive()` | 启动保活 | `None` |
| `stop_keepalive()` | 停止保活 | `None` |
| `update_cookie(new_cookie, save_to_config)` | 更新 Cookie | `None` |
| `get_qrcode()` | 获取登录二维码 | `(url, key)` |
| `check_login(qrcode_key)` | 检查登录状态 | `LoginStatus` |
| `close()` | 关闭服务 | `None` |

### 数据类

#### ServiceStatus
```python
@dataclass
class ServiceStatus:
    is_valid: bool          # 是否有效
    uid: int                # 用户 ID
    username: str           # 用户名
    vip_status: int         # VIP 状态
    is_login: bool          # 是否已登录
    check_time: str         # 检查时间
    message: str            # 状态消息
    remaining_days: int     # 剩余天数（估算）
```

#### LoginStatus
```python
@dataclass
class LoginStatus:
    success: bool           # 是否成功
    status: int             # 状态码
    message: str            # 状态消息
    cookie: str             # Cookie 字符串
    username: str           # 用户名
    uid: int                # 用户 ID
```

## 迁移指南

### 从 CookieManager 迁移

**旧代码：**
```python
from bili_monitor.api.cookie_manager import CookieManager

manager = CookieManager(cookie="...")
status = manager.check_cookie_status()
manager.start_keepalive()
```

**新代码：**
```python
from bili_monitor.api.cookie_service import CookieService

service = CookieService(cookie="...")
status = service.check_status()
service.start_keepalive()
```

### 从 CookieValidator 迁移

**旧代码：**
```python
from bili_monitor.api.cookie_manager import CookieValidator

validation = CookieValidator.validate(cookie)
```

**新代码：**
```python
# CookieValidator 仍然可用，作为底层实现
from bili_monitor.api.cookie_manager import CookieValidator

validation = CookieValidator.validate(cookie)

# 或使用服务层的独立检查函数
from bili_monitor.api.cookie_service import check_cookie_status_standalone

result = check_cookie_status_standalone(cookie)
```

## 优势

1. **统一接口**：所有 Cookie 相关操作通过一个类完成
2. **易于管理**：集中管理 Cookie 的保活、验证、更新
3. **自动持久化**：Cookie 更新后自动保存到配置文件
4. **状态追踪**：提供详细的 Cookie 状态信息
5. **扫码登录**：内置扫码登录支持

## 注意事项

1. CookieService 会自动管理保活线程，使用后请调用 `close()` 方法清理资源
2. 扫码登录成功后，Cookie 会自动保存到配置文件
3. Cookie 状态检查会访问 B 站 API，请注意频率控制
4. 保活功能默认每 30 分钟执行一次，可通过参数调整

## 示例代码

完整示例请参考：
- `bili_monitor/web/app.py` - Web 服务中的使用
- `bili_monitor/monitor.py` - 监控服务中的使用
