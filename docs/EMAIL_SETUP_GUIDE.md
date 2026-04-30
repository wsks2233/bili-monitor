# 邮件推送配置指南

## 概述

B 站 UP 主动态监控系统支持通过邮件推送动态更新通知。系统使用 SMTP 协议发送邮件，支持 SSL/TLS 加密，兼容主流邮件服务商。

---

## 配置步骤

### 1. 获取 SMTP 授权码

不同邮件服务商的获取方式不同，以下是常见服务商的配置方法：

#### 1.1 QQ 邮箱（推荐）

1. 登录 QQ 邮箱网页版
2. 点击「设置」→「账户」
3. 找到「POP3/IMAP/SMTP/Exchange/CardDAV/CalDAV 服务」
4. 开启「IMAP/SMTP 服务」
5. 点击「生成授权码」
6. 按提示发送短信验证
7. 获取 16 位授权码（不含空格）

**配置信息**：
- SMTP 服务器：`smtp.qq.com`
- SMTP 端口：`465` (SSL)
- 用户名：`你的 QQ 号@qq.com`
- 授权码：生成的 16 位授权码

#### 1.2 163 邮箱

1. 登录 163 邮箱网页版
2. 点击「设置」→「POP3/SMTP/IMAP」
3. 开启「IMAP/SMTP 服务」
4. 点击「客户端授权密码」
5. 设置授权密码（需要手机验证）

**配置信息**：
- SMTP 服务器：`smtp.163.com`
- SMTP 端口：`465` (SSL)
- 用户名：`你的用户名@163.com`
- 授权码：设置的授权密码

#### 1.3 Gmail

1. 登录 Google 账户
2. 开启两步验证
3. 访问 https://myaccount.google.com/apppasswords
4. 生成应用专用密码

**配置信息**：
- SMTP 服务器：`smtp.gmail.com`
- SMTP 端口：`587` (TLS) 或 `465` (SSL)
- 用户名：`你的用户名@gmail.com`
- 授权码：生成的 16 位应用密码

#### 1.4 Outlook/Hotmail

1. 登录 Microsoft 账户
2. 访问 https://account.microsoft.com/security
3. 开启两步验证
4. 生成应用密码

**配置信息**：
- SMTP 服务器：`smtp.office365.com`
- SMTP 端口：`587` (TLS)
- 用户名：`你的用户名@outlook.com`
- 授权码：生成的应用密码

#### 1.5 企业邮箱

以腾讯企业邮为例：
- SMTP 服务器：`smtp.exmail.qq.com`
- SMTP 端口：`465` (SSL)
- 用户名：`你的企业邮箱地址`
- 密码：企业邮箱密码（或客户端专用密码）

---

### 2. 修改配置文件

打开 `config.yaml` 文件，添加或修改 `notification` 部分：

```yaml
# 通知配置
notification:
  # 邮件通知配置
  - type: email
    smtp_server: "smtp.qq.com"           # SMTP 服务器地址
    smtp_port: 465                        # SMTP 端口（SSL 推荐 465，TLS 用 587）
    smtp_user: "123456789@qq.com"        # SMTP 用户名（完整邮箱地址）
    smtp_password: "abcdefghijklmnop"    # SMTP 授权码（不是邮箱密码！）
    sender: "123456789@qq.com"           # 发件人邮箱（通常与 smtp_user 相同）
    receivers:                            # 收件人列表（可以多个）
      - "receiver1@example.com"
      - "receiver2@example.com"
    use_ssl: true                         # 是否使用 SSL（推荐 true）
```

---

### 3. 配置参数说明

| 参数 | 必填 | 说明 | 示例 |
|------|------|------|------|
| `type` | ✅ | 通知类型，固定为 `email` | `email` |
| `smtp_server` | ✅ | SMTP 服务器地址 | `smtp.qq.com` |
| `smtp_port` | ✅ | SMTP 端口 | `465` (SSL) 或 `587` (TLS) |
| `smtp_user` | ✅ | SMTP 用户名 | `xxx@qq.com` |
| `smtp_password` | ✅ | SMTP 授权码 | `abcdefghijklmnop` |
| `sender` | ✅ | 发件人邮箱 | `xxx@qq.com` |
| `receivers` | ✅ | 收件人列表（数组） | `["a@example.com", "b@example.com"]` |
| `use_ssl` | ❌ | 是否使用 SSL（默认 true） | `true` 或 `false` |

---

### 4. 常见配置示例

#### 4.1 QQ 邮箱配置（最常用）

```yaml
notification:
  - type: email
    smtp_server: "smtp.qq.com"
    smtp_port: 465
    smtp_user: "123456789@qq.com"
    smtp_password: "abcdefghijklmnop"  # 16 位授权码
    sender: "123456789@qq.com"
    receivers:
      - "friend@example.com"
    use_ssl: true
```

#### 4.2 163 邮箱配置

```yaml
notification:
  - type: email
    smtp_server: "smtp.163.com"
    smtp_port: 465
    smtp_user: "yourname@163.com"
    smtp_password: "your_auth_code"  # 授权密码
    sender: "yourname@163.com"
    receivers:
      - "receiver@example.com"
    use_ssl: true
```

#### 4.3 Gmail 配置

```yaml
notification:
  - type: email
    smtp_server: "smtp.gmail.com"
    smtp_port: 587  # TLS 端口
    smtp_user: "yourname@gmail.com"
    smtp_password: "abcd efgh ijkl mnop"  # 16 位应用密码（可能含空格）
    sender: "yourname@gmail.com"
    receivers:
      - "receiver@example.com"
    use_ssl: false  # TLS 模式
```

#### 4.4 多收件人配置

```yaml
notification:
  - type: email
    smtp_server: "smtp.qq.com"
    smtp_port: 465
    smtp_user: "123456789@qq.com"
    smtp_password: "abcdefghijklmnop"
    sender: "123456789@qq.com"
    receivers:
      - "friend1@qq.com"
      - "friend2@163.com"
      - "friend3@gmail.com"
    use_ssl: true
```

#### 4.5 多个邮件通知配置

```yaml
notification:
  # 工作邮箱
  - type: email
    smtp_server: "smtp.qq.com"
    smtp_port: 465
    smtp_user: "work@qq.com"
    smtp_password: "work_auth_code"
    sender: "work@qq.com"
    receivers:
      - "colleague@company.com"
    use_ssl: true
  
  # 个人邮箱
  - type: email
    smtp_server: "smtp.163.com"
    smtp_port: 465
    smtp_user: "personal@163.com"
    smtp_password: "personal_auth_code"
    sender: "personal@163.com"
    receivers:
      - "myself@example.com"
    use_ssl: true
```

---

### 5. 测试邮件配置

#### 方法一：使用 Web 界面测试（推荐）

1. 启动 Web 服务：
   ```bash
   python web_main.py
   ```

2. 访问 Web 界面：`http://localhost:8000`

3. 进入「通知配置」页面

4. 添加邮件通知配置

5. 保存配置后，系统会自动测试连接

#### 方法二：使用测试脚本

创建测试脚本 `test_email.py`：

```python
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from bili_monitor.notification.email import EmailNotifier
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('test')

# 配置邮件参数
notifier = EmailNotifier(
    smtp_server="smtp.qq.com",
    smtp_port=465,
    smtp_user="123456789@qq.com",
    smtp_password="abcdefghijklmnop",
    sender="123456789@qq.com",
    receivers=["receiver@example.com"],
    use_ssl=True,
    logger=logger
)

# 测试发送
print("正在发送测试邮件...")
success = notifier.test()

if success:
    print("✓ 测试成功！邮件配置正确")
else:
    print("✗ 测试失败！请检查配置")
```

运行测试：
```bash
python test_email.py
```

#### 方法三：查看日志

启动监控服务后，查看日志文件：
```bash
tail -f logs/bili-monitor.log
```

成功的日志示例：
```
2026-03-03 22:00:00 - INFO - 邮件通知发送成功，接收者：1 人
```

失败的日志示例：
```
2026-03-03 22:00:00 - ERROR - 邮件通知发送异常：(535, b'Error: authentication failed')
```

---

### 6. 常见问题排查

#### 问题 1：认证失败 (535 Authentication Failed)

**原因**：
- 使用了邮箱密码而不是授权码
- 授权码输入错误
- SMTP 服务未开启

**解决方法**：
1. 确认已开启 SMTP 服务
2. 重新生成授权码
3. 检查授权码是否正确（无空格、大小写正确）
4. 确认用户名是完整邮箱地址

#### 问题 2：连接超时

**原因**：
- SMTP 服务器地址错误
- 端口被防火墙阻止
- 网络连接问题

**解决方法**：
1. 检查 SMTP 服务器地址是否正确
2. 尝试更换端口（465 ↔ 587）
3. 检查防火墙设置
4. 测试网络连接：`telnet smtp.qq.com 465`

#### 问题 3：需要 SSL/TLS

**原因**：
- 邮件服务商要求加密连接
- `use_ssl` 配置错误

**解决方法**：
- SSL 模式：`smtp_port: 465`, `use_ssl: true`
- TLS 模式：`smtp_port: 587`, `use_ssl: false`（会自动 starttls）

#### 问题 4：收件人被拒绝

**原因**：
- 收件人地址格式错误
- 发件人未通过验证

**解决方法**：
1. 检查收件人地址格式（`user@domain.com`）
2. 确保 `sender` 与 `smtp_user` 一致
3. 确认发件邮箱已通过验证

#### 问题 5：邮件进入垃圾箱

**原因**：
- 新邮箱信誉度低
- 邮件内容触发过滤规则

**解决方法**：
1. 将发件人添加到联系人
2. 标记邮件为「非垃圾邮件」
3. 使用信誉度高的邮箱（QQ、163 等）
4. 避免频繁发送（调整监控间隔）

---

### 7. 安全建议

1. **保护授权码**
   - 不要将授权码提交到 Git 仓库
   - 使用环境变量或加密存储
   - 定期更换授权码

2. **限制发送频率**
   - 设置合理的监控间隔（建议≥300 秒）
   - 避免短时间内大量发送邮件

3. **使用专用邮箱**
   - 建议使用专门的通知邮箱
   - 不要使用主邮箱

4. **启用两步验证**
   - 为邮箱开启两步验证
   - 使用应用专用密码

---

### 8. 完整配置示例

```yaml
# config.yaml

# 监控配置
monitor:
  check_interval: 300  # 5 分钟检查一次
  retry_times: 3
  retry_delay: 5
  cookie: "your_cookie_here"

# UP 主列表
upstreams:
  - uid: "546195"
    name: "老番茄"

# 日志配置
logger:
  level: INFO
  file: logs/bili-monitor.log
  max_bytes: 10485760
  backup_count: 5

# 数据库配置
database:
  path: data/bili_monitor.db

# 通知配置
notification:
  # QQ 邮箱推送
  - type: email
    smtp_server: "smtp.qq.com"
    smtp_port: 465
    smtp_user: "notify@qq.com"
    smtp_password: "your_auth_code_here"
    sender: "notify@qq.com"
    receivers:
      - "me@example.com"
    use_ssl: true
  
  # 企业微信机器人（可选，多个通知渠道）
  - type: wechat
    webhook_url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
```

---

### 9. 邮件内容预览

**邮件主题**：
```
【B 站动态】老番茄 发布了新动态
```

**纯文本内容**：
```
📢 B 站动态更新通知

👤 UP 主：老番茄
📝 类型：图文
🕐 时间：2026-03-03 22:00:00

📄 内容:
今天去拍了新的视频，大家期待一下！

🎬 视频：【老番茄】新视频预告
   BVID: BV1xx411c7mD

🖼️ 图片：3 张

👍 点赞：12,345
💬 评论：567
🔄 转发：890

🔗 链接：https://www.bilibili.com/opus/123456789
```

**HTML 内容**：
包含格式化排版、链接、样式等，更适合阅读。

---

### 10. 快速开始

**5 分钟快速配置**：

1. **获取授权码**（2 分钟）
   ```
   登录 QQ 邮箱 → 设置 → 账户 → 开启 SMTP → 生成授权码
   ```

2. **编辑配置文件**（1 分钟）
   ```bash
   # 复制示例配置
   cp config.example.yaml config.yaml
   
   # 编辑配置
   vim config.yaml
   ```

3. **添加邮件配置**（1 分钟）
   ```yaml
   notification:
     - type: email
       smtp_server: "smtp.qq.com"
       smtp_port: 465
       smtp_user: "你的 QQ 号@qq.com"
       smtp_password: "授权码"
       sender: "你的 QQ 号@qq.com"
       receivers:
         - "接收邮箱@example.com"
       use_ssl: true
   ```

4. **测试配置**（1 分钟）
   ```bash
   # 启动 Web 服务
   python web_main.py
   
   # 访问 http://localhost:8000
   # 查看是否能正常接收通知
   ```

---

## 技术支持

如遇到问题，请检查：
1. 日志文件：`logs/bili-monitor.log`
2. Web 界面错误提示
3. 邮箱的登录记录（确认是否被拦截）

**常见错误码**：
- `535`: 认证失败（检查授权码）
- `421`: 服务不可用（检查网络连接）
- `550`: 邮箱不存在（检查收件人地址）
- `452`: 邮箱已满（清理收件箱）

---

**更新日期**：2026-03-03  
**文档版本**：1.0
