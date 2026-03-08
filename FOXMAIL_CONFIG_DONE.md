# ✅ Foxmail 邮箱配置完成

## 配置信息

你的 Foxmail 邮箱已成功配置并测试通过！

### 📧 配置详情

```yaml
notification:
  - type: email
    smtp_server: "smtp.qq.com"
    smtp_port: 465
    smtp_user: "flowers2233@foxmail.com"
    smtp_password: "owkcemrmpigebiaf"  # 已配置
    sender: "flowers2233@foxmail.com"
    receivers:
      - "flowers2233@foxmail.com"
    use_ssl: true
```

### ✅ 测试结果

- **SMTP 连接**：✅ 成功
- **身份验证**：✅ 成功
- **邮件发送**：✅ 成功
- **测试邮件已发送至**：flowers2233@foxmail.com

---

## 📬 下一步操作

### 1. 检查测试邮件

请登录你的 Foxmail 邮箱，查看是否收到测试邮件。

**提示**：
- 如果没在收件箱找到，请检查**垃圾邮件箱**
- 将发件人添加到联系人可避免进入垃圾箱

### 2. 启动监控服务

#### 方式一：命令行模式
```bash
python main.py
```

#### 方式二：Web 界面模式
```bash
python web_main.py
```
然后访问：http://localhost:8000

### 3. 查看监控状态

查看日志文件：
```bash
tail -f logs/bili-monitor.log
```

成功的日志示例：
```
INFO - 邮件通知发送成功，接收者：1 人
```

---

## 🔔 通知触发条件

当监控的 UP 主（战国时代_姜汁汽水）发布新动态时，系统会：

1. ✅ 检测到新动态
2. ✅ 下载动态图片（如果有）
3. ✅ 保存到数据库
4. ✅ 发送邮件通知到你

---

## 📧 邮件内容示例

**邮件主题**：
```
【B 站动态】战国时代_姜汁汽水 发布了新动态
```

**邮件内容**：
```
📢 B 站动态更新通知

👤 UP 主：战国时代_姜汁汽水
📝 类型：图文
🕐 时间：2026-03-03 22:00:00

📄 内容:
[动态内容]

🔗 链接：https://www.bilibili.com/opus/xxxxxx
```

---

## ⚙️ 配置修改

### 修改接收邮箱

如果想发送给其他人，修改 `receivers` 部分：

```yaml
receivers:
  - "other@example.com"
```

### 添加多个接收人

```yaml
receivers:
  - "flowers2233@foxmail.com"
  - "someoneelse@example.com"
```

### 添加其他通知方式

可以同时配置微信、钉钉等多个通知渠道：

```yaml
notification:
  # Foxmail 邮箱
  - type: email
    smtp_server: "smtp.qq.com"
    smtp_port: 465
    smtp_user: "flowers2233@foxmail.com"
    smtp_password: "owkcemrmpigebiaf"
    sender: "flowers2233@foxmail.com"
    receivers:
      - "flowers2233@foxmail.com"
    use_ssl: true
  
  # 企业微信（可选）
  - type: wechat
    webhook_url: "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
```

---

## 🔧 常见问题

### Q: 如何停止邮件通知？

编辑 `config.yaml`，删除或注释掉 `notification` 部分：

```yaml
# notification:
#   - type: email
#     ...
```

### Q: 邮件发送太频繁怎么办？

增加检查间隔时间：

```yaml
monitor:
  check_interval: 600  # 改为 10 分钟检查一次
```

### Q: 更换邮箱怎么办？

1. 登录新邮箱获取授权码
2. 修改 `config.yaml` 中的邮箱配置
3. 重启监控服务

---

## 📊 配置备份

当前配置已保存到：[`config.yaml`](file:///f:/代码/github/bili-monitor/config.yaml)

建议定期备份配置文件：
```bash
cp config.yaml config.yaml.backup
```

---

## 📖 更多帮助

- 详细邮件配置指南：[EMAIL_SETUP_GUIDE.md](EMAIL_SETUP_GUIDE.md)
- 快速参考：[QUICK_EMAIL_SETUP.md](QUICK_EMAIL_SETUP.md)

---

**配置时间**：2026-03-03  
**配置状态**：✅ 已完成并测试通过  
**测试邮件**：✅ 已发送

祝你使用愉快！🎉
