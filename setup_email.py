#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
邮件配置快速设置工具
帮助用户快速配置邮件通知功能
"""

import os
import sys
import yaml

def print_banner():
    print("=" * 70)
    print("B 站 UP 主动态监控 - 邮件通知配置工具")
    print("=" * 70)
    print()

def print_step(step_num, description):
    print(f"\n【步骤 {step_num}】{description}")
    print("-" * 70)

def input_with_default(prompt, default=None, required=False):
    """获取用户输入，支持默认值"""
    if default:
        prompt = f"{prompt} [{default}]: "
    else:
        prompt = f"{prompt}: "
    
    while True:
        value = input(prompt).strip()
        if not value and default:
            return default
        if not value and required:
            print("❌ 此项为必填项，请输入内容")
            continue
        return value

def select_email_provider():
    """选择邮件服务商"""
    print("\n请选择你的邮件服务商：")
    print("  1. QQ 邮箱（推荐）")
    print("  2. 163 邮箱")
    print("  3. Gmail")
    print("  4. Outlook/Hotmail")
    print("  5. 其他（手动配置）")
    
    while True:
        choice = input("请输入选项 (1-5): ").strip()
        if choice in ['1', '2', '3', '4', '5']:
            return choice
    
    return '1'

def get_provider_config(choice):
    """根据选择返回邮件服务商配置"""
    providers = {
        '1': {
            'name': 'QQ 邮箱',
            'smtp_server': 'smtp.qq.com',
            'smtp_port': 465,
            'help_url': 'https://mail.qq.com/cgi-bin/help?subtype=1&&id=28&&no=1001256',
            'tips': '需要在 QQ 邮箱设置中开启 SMTP 服务并获取授权码'
        },
        '2': {
            'name': '163 邮箱',
            'smtp_server': 'smtp.163.com',
            'smtp_port': 465,
            'help_url': 'https://help.mail.163.com/faqDetail.do?code=d7a5dc8471cd0c0e8b4b8f4f38c673fd1c731c4d1c84a18c',
            'tips': '需要在 163 邮箱设置中开启 SMTP 服务并设置授权密码'
        },
        '3': {
            'name': 'Gmail',
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'help_url': 'https://support.google.com/accounts/answer/185833',
            'tips': '需要开启两步验证并生成应用专用密码'
        },
        '4': {
            'name': 'Outlook/Hotmail',
            'smtp_server': 'smtp.office365.com',
            'smtp_port': 587,
            'help_url': 'https://support.microsoft.com/zh-cn/office/outlook-com-%E7%9A%84-pop-%E5%92%8C-imap%E8%AE%BE%E7%BD%AE-95fe5f09-661d-479c-93f6-5d6cad4dc4d5',
            'tips': '需要开启两步验证并生成应用密码'
        },
        '5': {
            'name': '其他',
            'smtp_server': None,
            'smtp_port': None,
            'help_url': None,
            'tips': '请手动配置 SMTP 服务器和端口'
        }
    }
    return providers.get(choice, providers['1'])

def load_existing_config(config_path):
    """加载现有配置"""
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f) or {}
    return {}

def save_config(config, config_path):
    """保存配置到文件"""
    # 备份现有配置
    if os.path.exists(config_path):
        backup_path = config_path + '.backup'
        os.rename(config_path, backup_path)
        print(f"✓ 已备份原配置文件为：{backup_path}")
    
    # 保存新配置
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, allow_unicode=True, default_flow_style=False)
    
    print(f"✓ 配置已保存到：{config_path}")

def main():
    print_banner()
    
    config_path = input_with_default("配置文件路径", "config.yaml")
    
    # 加载现有配置
    config = load_existing_config(config_path)
    
    # 步骤 1：选择邮件服务商
    print_step(1, "选择邮件服务商")
    provider_choice = select_email_provider()
    provider = get_provider_config(provider_choice)
    
    print(f"\n✓ 已选择：{provider['name']}")
    if provider['tips']:
        print(f"💡 提示：{provider['tips']}")
    if provider['help_url']:
        print(f"📖 帮助文档：{provider['help_url']}")
    
    # 步骤 2：配置 SMTP 服务器
    print_step(2, "配置 SMTP 服务器")
    
    if provider['smtp_server']:
        smtp_server = input_with_default("SMTP 服务器", provider['smtp_server'], required=True)
        smtp_port = input_with_default("SMTP 端口", str(provider['smtp_port']), required=True)
    else:
        smtp_server = input_with_default("SMTP 服务器地址", required=True)
        smtp_port = input_with_default("SMTP 端口", "465", required=True)
    
    use_ssl = input_with_default("是否使用 SSL (true/false)", "true")
    use_ssl = use_ssl.lower() in ['true', 'yes', '1', 'y']
    
    # 步骤 3：配置邮箱账号
    print_step(3, "配置邮箱账号")
    
    smtp_user = input_with_default("SMTP 用户名（完整邮箱地址）", required=True)
    smtp_password = input_with_default("SMTP 授权码（不是邮箱密码！）", required=True)
    sender = input_with_default("发件人邮箱", smtp_user, required=True)
    
    # 步骤 4：配置收件人
    print_step(4, "配置收件人")
    print("请输入收件人邮箱地址，多个收件人用逗号分隔")
    receivers_input = input_with_default("收件人邮箱列表", required=True)
    receivers = [r.strip() for r in receivers_input.split(',') if r.strip()]
    
    # 步骤 5：确认配置
    print_step(5, "确认配置信息")
    
    email_config = {
        'type': 'email',
        'smtp_server': smtp_server,
        'smtp_port': int(smtp_port),
        'smtp_user': smtp_user,
        'smtp_password': smtp_password,
        'sender': sender,
        'receivers': receivers,
        'use_ssl': use_ssl
    }
    
    print("\n配置信息：")
    print(f"  邮件服务商：{provider['name']}")
    print(f"  SMTP 服务器：{smtp_server}:{smtp_port}")
    print(f"  发件人：{sender}")
    print(f"  收件人：{', '.join(receivers)}")
    print(f"  SSL 加密：{'是' if use_ssl else '否'}")
    
    confirm = input("\n确认保存配置？(y/n): ").strip().lower()
    if confirm != 'y':
        print("❌ 配置已取消")
        return
    
    # 保存配置
    if 'notification' not in config:
        config['notification'] = []
    
    # 检查是否已有邮件配置
    email_exists = any(n.get('type') == 'email' for n in config['notification'])
    if email_exists:
        print("\n⚠️  检测到已有邮件配置，是否覆盖？")
        overwrite = input("确认覆盖？(y/n): ").strip().lower()
        if overwrite == 'y':
            config['notification'] = [n for n in config['notification'] if n.get('type') != 'email']
        else:
            print("❌ 配置已取消")
            return
    
    config['notification'].append(email_config)
    save_config(config, config_path)
    
    # 步骤 6：测试配置（可选）
    print_step(6, "测试邮件配置（可选）")
    test_now = input("是否立即发送测试邮件？(y/n): ").strip().lower()
    
    if test_now == 'y':
        print("\n正在发送测试邮件...")
        try:
            from bili_monitor.notification.email import EmailNotifier
            import logging
            
            logging.basicConfig(level=logging.INFO)
            logger = logging.getLogger('email_test')
            
            notifier = EmailNotifier(
                smtp_server=smtp_server,
                smtp_port=int(smtp_port),
                smtp_user=smtp_user,
                smtp_password=smtp_password,
                sender=sender,
                receivers=receivers[:1],  # 只发送给第一个收件人
                use_ssl=use_ssl,
                logger=logger
            )
            
            success = notifier.test()
            
            if success:
                print("\n✅ 测试成功！邮件已发送")
                print(f"请检查以下邮箱：{receivers[0]}")
            else:
                print("\n❌ 测试失败！请检查配置")
                print("\n常见问题：")
                print("  1. 确认 SMTP 服务已开启")
                print("  2. 确认授权码正确（不是邮箱密码）")
                print("  3. 检查网络连接")
                print("  4. 查看日志文件获取详细错误信息")
        except ImportError:
            print("⚠️  无法导入邮件模块，跳过测试")
        except Exception as e:
            print(f"❌ 测试失败：{e}")
    
    # 完成
    print("\n" + "=" * 70)
    print("配置完成！")
    print("=" * 70)
    print("\n下一步：")
    print("  1. 启动监控服务：python main.py")
    print("  2. 或启动 Web 服务：python web_main.py")
    print("  3. 查看日志确认邮件发送状态：tail -f logs/bili-monitor.log")
    print("\n💡 提示：")
    print("  - 如果收到垃圾邮件，请将发件人添加到联系人")
    print("  - 可以配置多个通知渠道（微信、钉钉等）")
    print("  - 详细文档请查看：EMAIL_SETUP_GUIDE.md")
    print()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ 配置已中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 发生错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
