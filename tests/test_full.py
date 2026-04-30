#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B站UP主动态监控系统 - 全面功能测试脚本

运行方式: python -m tests.test_full
或从项目根目录: python tests/test_full.py
"""

import sys
import os
import time
import traceback

# 添加项目根目录到Python路径
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from bili_monitor.core.config import load_config, Config, MonitorConfig, UpstreamConfig
from bili_monitor.core.logger import setup_logger, LoggerConfig
from bili_monitor.storage.database import Database, DatabaseConfig
from bili_monitor.api.bili_api import BiliAPI
from bili_monitor.monitor import Monitor


def test_config_loading():
    """测试1: 配置文件加载"""
    print("\n" + "="*60)
    print("测试1: 配置文件加载功能")
    print("="*60)
    
    try:
        config = load_config()
        print(f"[OK] 配置文件加载成功")
        print(f"  - 监控间隔: {config.monitor.check_interval} 秒")
        print(f"  - 重试次数: {config.monitor.retry_times}")
        print(f"  - UP主数量: {len(config.upstreams)}")
        
        for i, upstream in enumerate(config.upstreams):
            print(f"  - UP主{i+1}: {upstream.name} (UID: {upstream.uid})")
        
        print(f"  - 数据库路径: {config.database.path}")
        print(f"  - Web端口: {config.web.port}")
        print(f"  - 通知配置数量: {len(config.notification)}")
        
        for i, notif in enumerate(config.notification):
            print(f"  - 通知方式{i+1}: {notif.get('type', '未知')}")
        
        return True
    except FileNotFoundError as e:
        print(f"[FAIL] 配置文件加载失败: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] 配置文件加载异常: {e}")
        traceback.print_exc()
        return False


def test_logger_setup():
    """测试2: 日志系统初始化"""
    print("\n" + "="*60)
    print("测试2: 日志系统初始化")
    print("="*60)
    
    try:
        config = load_config()
        logger = setup_logger(config.logger)
        print(f"[OK] 日志系统初始化成功")
        print(f"  - 日志级别: {config.logger.level}")
        print(f"  - 日志文件: {config.logger.file}")
        
        logger.info("测试日志输出")
        print(f"  [OK] 测试日志写入成功")
        
        return True
    except Exception as e:
        print(f"[FAIL] 日志系统初始化失败: {e}")
        traceback.print_exc()
        return False


def test_database():
    """测试3: 数据库连接和初始化"""
    print("\n" + "="*60)
    print("测试3: 数据库连接和初始化")
    print("="*60)
    
    try:
        config = load_config()
        logger = setup_logger(config.logger)
        
        db = Database(config.database, logger)
        print(f"[OK] 数据库连接成功")
        print(f"  - 数据库路径: {config.database.path}")
        
        stats = db.get_stats()
        print(f"  [OK] 获取统计信息成功:")
        print(f"    - 总动态数: {stats['total_dynamics']}")
        print(f"    - 总UP主数: {stats['total_upstreams']}")
        
        db.close()
        print(f"[OK] 数据库关闭正常")
        
        return True
    except Exception as e:
        print(f"[FAIL] 数据库操作失败: {e}")
        traceback.print_exc()
        return False


def test_bili_api_user_info():
    """测试4: B站API - 用户信息获取"""
    print("\n" + "="*60)
    print("测试4: B站API - 用户信息获取")
    print("="*60)
    
    try:
        config = load_config()
        logger = setup_logger(config.logger)
        api = BiliAPI(logger, cookie=config.monitor.cookie)
        
        if not config.upstreams:
            print("[FAIL] 没有配置UP主，跳过测试")
            return False
        
        upstream = config.upstreams[0]
        print(f"测试UP主: {upstream.name} (UID: {upstream.uid})")
        
        user_info = api.get_user_info(upstream.uid)
        if user_info:
            print(f"[OK] 获取用户信息成功:")
            print(f"  - 名称: {user_info.name}")
            print(f"  - 等级: {user_info.level}")
            print(f"  - 签名: {(user_info.sign or '无')[:30]}...")
            
            fans = api.get_user_fans(upstream.uid)
            print(f"  - 粉丝数: {fans:,}")
            
            api.close()
            return True
        else:
            print(f"[FAIL] 获取用户信息失败")
            api.close()
            return False
            
    except Exception as e:
        print(f"[FAIL] API调用异常: {e}")
        traceback.print_exc()
        return False


def test_bili_api_dynamics():
    """测试5: B站API - 动态获取"""
    print("\n" + "="*60)
    print("测试5: B站API - 动态获取")
    print("="*60)
    
    try:
        config = load_config()
        logger = setup_logger(config.logger)
        api = BiliAPI(logger, cookie=config.monitor.cookie)
        
        if not config.upstreams:
            print("[FAIL] 没有配置UP主，跳过测试")
            return False
        
        upstream = config.upstreams[0]
        print(f"获取动态: {upstream.name} (UID: {upstream.uid})")
        
        dynamics = api.get_user_dynamics(upstream.uid, limit=5)
        
        if dynamics:
            print(f"[OK] 成功获取 {len(dynamics)} 条动态:")
            for i, dynamic in enumerate(dynamics[:3], 1):
                print(f"\n  动态{i}:")
                print(f"    ID: {dynamic.dynamic_id[:20]}...")
                print(f"    类型: {dynamic.dynamic_type}")
                content_preview = dynamic.content[:50] + "..." if len(dynamic.content) > 50 else dynamic.content
                print(f"    内容: {content_preview}")
                print(f"    发布时间: {dynamic.publish_time}")
                print(f"    点赞/转发/评论: {dynamic.stat.like}/{dynamic.stat.repost}/{dynamic.stat.comment}")
                
                if dynamic.video:
                    print(f"    视频: {dynamic.video.title}")
                
                if dynamic.images:
                    print(f"    图片: {len(dynamic.images)} 张")
            
            api.close()
            return True
        else:
            print(f"⚠ 未获取到动态（可能该用户暂无公开动态）")
            api.close()
            return True
            
    except Exception as e:
        print(f"[FAIL] API调用异常: {e}")
        traceback.print_exc()
        return False


def test_database_operations():
    """测试6: 数据库完整操作（增删改查）"""
    print("\n" + "="*60)
    print("测试6: 数据库完整操作")
    print("="*60)
    
    try:
        from bili_monitor.core.models import DynamicInfo, StatInfo, ImageInfo
        
        config = load_config()
        logger = setup_logger(config.logger)
        db = Database(config.database, logger)
        
        # 测试保存UP主信息
        from datetime import datetime
        test_upstream = type('UpstreamInfo', (), {
            'uid': 'test_uid_001',
            'name': '测试用户',
            'face': '',
            'sign': '测试签名',
            'level': 6,
            'fans': 10000,
        })()
        
        if db.save_upstream(test_upstream):
            print(f"[OK] 保存UP主信息成功")
        
        # 测试查询UP主
        upstream = db.get_upstream('test_uid_001')
        if upstream and upstream.name == '测试用户':
            print(f"[OK] 查询UP主信息成功: {upstream.name}")
        
        # 测试保存动态
        test_dynamic = DynamicInfo(
            dynamic_id='test_dynamic_001',
            uid='test_uid_001',
            upstream_name='测试用户',
            dynamic_type='DYNAMIC_TYPE_WORD',
            content='这是一条测试动态内容',
            publish_time=datetime.now(),
            create_time=datetime.now(),
            images=[ImageInfo(url='http://example.com/test.jpg')],
            video=None,
            stat=StatInfo(like=100, repost=50, comment=20),
            raw_json={'test': 'data'},
        )
        
        if db.save_dynamic(test_dynamic):
            print(f"[OK] 保存动态成功")
        
        # 测试查询动态是否存在
        if db.dynamic_exists('test_dynamic_001'):
            print(f"[OK] 动态存在性检查通过")
        
        # 测试获取已处理ID列表
        processed_ids = db.get_processed_ids('test_uid_001')
        if 'test_dynamic_001' in processed_ids:
            print(f"[OK] 已处理ID列表查询正确")
        
        # 测试获取动态列表
        dynamics_list = db.get_dynamics(uid='test_uid_001', limit=10)
        if dynamics_list:
            print(f"[OK] 动态列表查询成功，共 {len(dynamics_list)} 条")
        
        # 清理测试数据
        cursor = db.conn.cursor()
        cursor.execute("DELETE FROM dynamics WHERE dynamic_id LIKE 'test_%'")
        cursor.execute("DELETE FROM upstreams WHERE uid LIKE 'test_%'")
        db.conn.commit()
        print(f"[OK] 测试数据清理完成")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"[FAIL] 数据库操作异常: {e}")
        traceback.print_exc()
        return False


def test_notification_system():
    """测试7: 通知系统初始化"""
    print("\n" + "="*60)
    print("测试7: 通知系统初始化")
    print("="*60)
    
    try:
        config = load_config()
        logger = setup_logger(config.logger)
        
        from bili_monitor.notification import create_notifier
        
        if not config.notification:
            print("⚠ 未配置通知方式，跳过通知测试")
            return True
        
        notifiers = []
        for i, notifier_cfg in enumerate(config.notification):
            try:
                notifier_type = notifier_cfg.get('type', '')
                notifier_config = notifier_cfg.copy()
                notifier_config.pop('type', None)
                
                notifier = create_notifier(notifier_type, **notifier_config)
                notifiers.append((notifier_type, notifier))
                print(f"[OK] 通知器{i+1}初始化成功: {notifier_type}")
                
            except Exception as e:
                print(f"[FAIL] 通知器{i+1}({notifier_type})初始化失败: {e}")
        
        if notifiers:
            print(f"\n[OK] 共成功初始化 {len(notifiers)} 个通知器")
            
            # 注意：这里不实际发送通知，只测试初始化
            print(f"⚠ 提示：未执行实际通知发送（避免产生垃圾消息）")
        
        return True
        
    except Exception as e:
        print(f"[FAIL] 通知系统异常: {e}")
        traceback.print_exc()
        return False


def test_web_app():
    """测试8: Web应用启动"""
    print("\n" + "="*60)
    print("测试8: Web应用启动测试")
    print("="*60)
    
    try:
        config = load_config()
        logger = setup_logger(config.logger)
        
        # 测试导入Web模块
        from bili_monitor.web.app import app
        
        print(f"[OK] Web应用导入成功")
        print(f"  - FastAPI实例已创建")
        
        # 检查路由
        routes = [route.path for route in app.routes if hasattr(route, 'path')]
        print(f"  - 注册路由数: {len(routes)}")
        
        for route in routes[:10]:
            print(f"    • {route}")
        
        return True
        
    except ImportError as e:
        print(f"⚠ Web模块导入可能缺少依赖: {e}")
        return False
    except Exception as e:
        print(f"[FAIL] Web应用启动异常: {e}")
        traceback.print_exc()
        return False


def test_cookie_service():
    """测试9: Cookie服务"""
    print("\n" + "="*60)
    print("测试9: Cookie服务检查")
    print("="*60)
    
    try:
        config = load_config()
        logger = setup_logger(config.logger)
        
        from bili_monitor.api.cookie_service import CookieService
        
        if not config.monitor.cookie:
            print("⚠ 未配置Cookie，跳过Cookie服务测试")
            return True
        
        cookie_service = CookieService(
            cookie=config.monitor.cookie,
            config_path=os.path.join(PROJECT_ROOT, "config.yaml"),
            logger=logger,
        )
        
        status = cookie_service.check_status()
        print(f"[OK] Cookie状态检查完成:")
        print(f"  - 是否有效: {status.is_valid}")
        print(f"  - 状态消息: {status.message}")
        
        if status.username:
            print(f"  - 用户名: {status.username}")
        if status.uid:
            print(f"  - UID: {status.uid}")
        if status.remaining_days is not None:
            print(f"  - 剩余天数: {status.remaining_days}")
        
        cookie_service.close()
        return True
        
    except Exception as e:
        print(f"[FAIL] Cookie服务异常: {e}")
        traceback.print_exc()
        return False


def run_all_tests():
    """运行所有测试"""
    print("\n" + "#"*70)
    print("#" + " "*68 + "#")
    print("#" + "  B站UP主动态监控系统 - 全面功能测试".center(62) + "#")
    print("#" + " "*68 + "#")
    print("#"*70)
    
    results = {}
    
    tests = [
        ("配置文件加载", test_config_loading),
        ("日志系统", test_logger_setup),
        ("数据库连接", test_database),
        ("B站API-用户信息", test_bili_api_user_info),
        ("B站API-动态获取", test_bili_api_dynamics),
        ("数据库操作", test_database_operations),
        ("通知系统", test_notification_system),
        ("Web应用", test_web_app),
        ("Cookie服务", test_cookie_service),
    ]
    
    for name, test_func in tests:
        try:
            result = test_func()
            results[name] = result
        except Exception as e:
            print(f"\n[FAIL] 测试 '{name}' 发生未捕获异常: {e}")
            results[name] = False
    
    # 输出测试总结
    print("\n" + "#"*70)
    print("# 测试结果总结".center(66) + "#")
    print("#"*70)
    
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    
    for name, result in results.items():
        status = "[OK] 通过" if result else "[FAIL] 失败"
        print(f"#  {name:<20} {status}".ljust(65) + "#")
    
    print("#" + "-"*68 + "#")
    print(f"#  总计: {passed}/{total} 通过".ljust(65) + "#")
    print("#"*70)
    
    if passed == total:
        print("\n🎉 所有测试通过！项目功能正常运行。")
    else:
        failed_tests = [name for name, result in results.items() if not result]
        print(f"\n⚠️ 有 {total - passed} 个测试失败：")
        for test_name in failed_tests:
            print(f"  - {test_name}")
    
    return passed == total


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
