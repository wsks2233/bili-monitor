# 邮件推送快速配置

## 📧 三种配置方式

### 方式一：使用配置工具（推荐）

```bash
python setup_email.py
```

按提示操作即可，支持：
- ✅ 自动选择邮件服务商
- ✅ 智能填写默认值
- ✅ 配置验证和测试
- ✅ 自动备份原配置

---

### 方式二：手动编辑配置文件

编辑 `config.yaml`，添加以下内容：

```yaml
notification:
  - type: email
    smtp_server: "smtp.qq.com"
    smtp_port: 465
    smtp_user: "你的 QQ 号@qq.com"
    smtp_password: "你的授权码"
    sender: "你的 QQ 号@qq.com"
    receivers:
      - "接收邮箱@example.com"
    use_ssl: true
```

---

### 方式三：Web 界面配置

1. 启动 Web 服务：`python web_main.py`
2. 访问：`http://localhost:8000`
3. 进入「通知配置」标签页
4. 添加邮件通知配置
5. 保存并测试

---

## 🔑 获取授权码（以 QQ 邮箱为例）

1. 登录 QQ 邮箱网页版
2. 点击「设置」→「账户」
3. 开启「POP3/SMTP 服务」
4. 点击「生成授权码」
5. 发送短信验证
6. 复制 16 位授权码

**注意**：授权码不是邮箱密码！

---

## 📝 常见邮件服务商配置

| 服务商 | SMTP 服务器 | 端口 | SSL |
|--------|------------|------|-----|
| QQ 邮箱 | smtp.qq.com | 465 | ✅ |
| 163 邮箱 | smtp.163.com | 465 | ✅ |
| Gmail | smtp.gmail.com | 587 | ❌ (TLS) |
| Outlook | smtp.office365.com | 587 | ❌ (TLS) |

---

## ✅ 验证配置

### 方法 1：查看日志
```bash
tail -f logs/bili-monitor.log
```

成功日志：
```
INFO - 邮件通知发送成功，接收者：1 人
```

### 方法 2：测试发送
```bash
python setup_email.py
# 选择测试选项
```

---

## ❗ 常见问题

**Q: 认证失败 (535 Error)**
- 使用授权码，不是邮箱密码
- 确认 SMTP 服务已开启

**Q: 连接超时**
- 检查 SMTP 服务器地址
- 检查防火墙设置
- 尝试更换端口

**Q: 邮件进入垃圾箱**
- 将发件人添加到联系人
- 使用信誉度高的邮箱

---

## 📖 详细文档

查看完整配置指南：[EMAIL_SETUP_GUIDE.md](EMAIL_SETUP_GUIDE.md)

---

**快速开始**：
```bash
# 1. 运行配置工具
python setup_email.py

# 2. 启动服务
python main.py  # 或 python web_main.py

# 3. 等待动态更新通知
```
