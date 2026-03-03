# 配置保存卡死问题修复说明

## 问题描述

用户在 Web 界面点击"保存配置"按钮后，前端出现卡死现象，无法完成配置保存操作。

## 问题原因分析

### 1. **CookieService 线程锁阻塞**

在 `bili_monitor/api/cookie_service.py` 的 `update_cookie()` 方法中使用了线程锁：

```python
def update_cookie(self, new_cookie: str, save_to_config: bool = True):
    with self._lock:  # 这里会无限期等待锁
        # 停止保活、更新 Cookie、重启保活
```

**问题**：
- 当 Cookie 保活线程正在执行时，Web 请求线程可能无法获取锁
- 没有超时机制，导致无限期等待
- 如果保活线程也在尝试获取同一个锁，可能造成死锁

### 2. **配置保存逻辑过于复杂**

原来的配置保存流程：
1. 保存配置文件
2. 停止监控服务
3. 关闭 Cookie 服务
4. 重新创建监控实例
5. 重新创建 Cookie 服务
6. 重启监控服务

**问题**：
- 涉及多个全局变量的修改
- 需要停止和重启多个服务
- 操作时间长，容易导致前端超时

### 3. **前端缺少超时机制**

前端的 API 调用没有设置超时：

```javascript
async post(url, data = null) {
    const res = await fetch(url, {
        method: 'POST',
        body: JSON.stringify(data)
    });
    // 没有超时控制
}
```

**问题**：
- 后端阻塞时，前端会无限期等待
- 用户体验差，界面卡死

## 解决方案

### 1. **优化 CookieService 的锁机制**

**文件**: `bili_monitor/api/cookie_service.py`

**修改**：
```python
def update_cookie(self, new_cookie: str, save_to_config: bool = True, timeout: float = 5.0):
    """
    更新 Cookie
    
    Args:
        new_cookie: 新的 Cookie
        save_to_config: 是否保存到配置文件
        timeout: 获取锁的超时时间（秒）
    """
    acquired = self._lock.acquire(timeout=timeout)
    if not acquired:
        self.logger.warning(f"获取 Cookie 更新锁超时，跳过更新")
        return False
    
    try:
        # 更新逻辑
        return True
    finally:
        self._lock.release()
```

**改进**：
- ✅ 添加超时机制（默认 5 秒）
- ✅ 获取锁失败时返回 False 而不是阻塞
- ✅ 使用 try-finally 确保锁被释放

### 2. **简化配置保存流程**

**文件**: `bili_monitor/web/app.py`

**修改**：
```python
@app.post("/api/config")
async def update_config(config_data: ConfigModel):
    # 1. 保存配置文件（快速操作）
    # ...
    
    # 2. 只更新 Cookie 服务（如果 Cookie 变化）
    if cookie_service and new_cookie and new_cookie != existing_cookie:
        try:
            cookie_service.update_cookie(new_cookie, save_to_config=False)
        except Exception as e:
            logger.warning(f"更新 Cookie 服务失败：{e}，但配置已保存")
    
    # 3. 热更新监控配置（不重启服务）
    if monitor_instance and monitor_instance.running:
        try:
            new_config = load_config(config_path)
            monitor_instance.config = new_config
        except Exception as e:
            logger.warning(f"热更新配置失败：{e}，但配置已保存")
    
    return {"success": True, "message": "配置已保存"}
```

**改进**：
- ✅ 不再停止和重启监控服务
- ✅ 采用热更新方式修改配置
- ✅ 即使更新失败也返回成功（配置已保存到文件）
- ✅ 减少全局变量操作

### 3. **前端添加超时控制**

**文件**: `bili_monitor/web/static/index.html`

**修改**：
```javascript
const api = {
    async get(url, timeout = 10000) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeout);
        
        try {
            const res = await fetch(url, { signal: controller.signal });
            clearTimeout(timeoutId);
            
            if (!res.ok) {
                throw new Error('请求失败');
            }
            return res.json();
        } catch (e) {
            clearTimeout(timeoutId);
            if (e.name === 'AbortError') {
                throw new Error('请求超时，请稍后再试');
            }
            throw e;
        }
    },
    async post(url, data = null, timeout = 15000) {
        // 类似的超时控制
    }
};
```

**改进**：
- ✅ GET 请求超时：10 秒
- ✅ POST 请求超时：15 秒
- ✅ 超时后显示友好提示
- ✅ 使用 AbortController 取消请求

## 测试验证

### 测试 1：基本配置保存
```bash
python test_config_save.py
```

**结果**：✅ 通过
- 配置加载成功
- Cookie 服务更新正常（0.00 秒）
- 配置热更新完成
- 资源清理完成

### 测试 2：并发场景测试
```bash
python test_web_config_save.py
```

**结果**：✅ 通过
- 配置保存成功（0.00 秒）
- 未出现阻塞
- 热更新正常工作

## 使用建议

### 1. **配置修改后的行为**

- ✅ **保存配置**：配置立即保存到文件
- ✅ **热更新**：如果监控正在运行，配置会立即生效
- ⚠️ **Cookie 更新**：如果 Cookie 变化，会更新 Cookie 服务
- ℹ️ **无需重启**：大部分配置修改无需重启监控服务

### 2. **特殊情况**

某些配置修改可能需要重启监控才能完全生效：
- 数据库路径修改
- 日志文件路径修改
- 日志级别修改（部分生效）

如果遇到配置不生效的情况，建议：
1. 先停止监控
2. 修改配置
3. 重新启动监控

### 3. **超时配置**

前端 API 调用已设置超时：
- 普通请求：10 秒
- 配置保存：15 秒

如果网络环境较差，可以适当增加超时时间：

```javascript
// 在 index.html 中修改
async post(url, data = null, timeout = 30000) {  // 改为 30 秒
    // ...
}
```

## 技术总结

### 核心改进

1. **线程安全**：使用带超时的锁机制，避免死锁
2. **热更新**：支持配置热更新，无需重启服务
3. **超时控制**：前后端都添加了超时保护
4. **错误隔离**：即使更新失败，配置也会保存成功

### 最佳实践

1. ✅ **避免长时间持有锁**：锁操作应该快速完成
2. ✅ **使用超时机制**：任何可能阻塞的操作都应该有超时
3. ✅ **优雅降级**：部分操作失败不影响整体流程
4. ✅ **用户友好**：超时后显示清晰的错误提示

## 相关文件

- `bili_monitor/api/cookie_service.py` - Cookie 服务（已优化）
- `bili_monitor/web/app.py` - Web API（已优化）
- `bili_monitor/web/static/index.html` - 前端页面（已优化）
- `test_config_save.py` - 配置保存测试
- `test_web_config_save.py` - Web 配置保存测试

## 更新日期

2026-03-03
