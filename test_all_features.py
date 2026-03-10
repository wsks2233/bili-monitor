#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目全面功能测试脚本
测试所有核心模块功能
"""

import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('test_all')

def test_config():
    """测试配置模块"""
    logger.info("\n" + "="*50)
    logger.info("测试 1: 配置模块 (config.py)")
    logger.info("="*50)
    
    try:
        from bili_monitor.core.config import load_config, Config
        config = load_config()
        logger.info(f"✅ 配置加载成功")
        logger.info(f"   - 监控间隔: {config.monitor.check_interval}秒")
        logger.info(f"   - UP主数量: {len(config.upstreams)}")
        logger.info(f"   - 数据库路径: {config.database.path}")
        return True
    except Exception as e:
        logger.error(f"❌ 配置模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_logger():
    """测试日志模块"""
    logger.info("\n" + "="*50)
    logger.info("测试 2: 日志模块 (logger.py)")
    logger.info("="*50)
    
    try:
        from bili_monitor.core.logger import setup_logger
        from bili_monitor.core.config import LoggerConfig
        
        log_config = LoggerConfig(
            level="DEBUG",
            file="test.log",
            max_bytes=1024*1024,
            backup_count=1
        )
        test_logger = setup_logger(log_config)
        test_logger.debug("测试DEBUG日志")
        test_logger.info("测试INFO日志")
        test_logger.warning("测试WARNING日志")
        logger.info("✅ 日志模块测试成功")
        return True
    except Exception as e:
        logger.error(f"❌ 日志模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_models():
    """测试数据模型"""
    logger.info("\n" + "="*50)
    logger.info("测试 3: 数据模型 (models.py)")
    logger.info("="*50)
    
    try:
        from bili_monitor.core.models import (
            DynamicInfo, UpstreamInfo, StatInfo, 
            VideoInfo, ImageInfo
        )
        from datetime import datetime
        
        stat = StatInfo(like=100, repost=20, comment=30)
        logger.info(f"   ✅ StatInfo 创建成功: {stat.to_dict()}")
        
        image = ImageInfo(url="https://example.com/image.jpg", width=800, height=600)
        logger.info(f"   ✅ ImageInfo 创建成功")
        
        video = VideoInfo(bvid="BV1xx411c7mD", aid=12345, title="测试视频")
        logger.info(f"   ✅ VideoInfo 创建成功")
        
        dynamic = DynamicInfo(
            dynamic_id="123456789",
            uid="123456",
            upstream_name="测试UP主",
            dynamic_type="图文",
            content="测试内容",
            publish_time=datetime.now(),
            images=[image],
            video=video,
            stat=stat
        )
        logger.info(f"   ✅ DynamicInfo 创建成功")
        logger.info(f"      - 动态ID: {dynamic.dynamic_id}")
        logger.info(f"      - 内容长度: {len(dynamic.content)}")
        
        upstream = UpstreamInfo(uid="123456", name="测试UP主")
        logger.info(f"   ✅ UpstreamInfo 创建成功")
        
        logger.info("✅ 数据模型测试成功")
        return True
    except Exception as e:
        logger.error(f"❌ 数据模型测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database():
    """测试数据库模块"""
    logger.info("\n" + "="*50)
    logger.info("测试 4: 数据库模块 (database.py)")
    logger.info("="*50)
    
    try:
        from bili_monitor.storage.database import Database
        from bili_monitor.core.config import DatabaseConfig
        from bili_monitor.core.models import DynamicInfo, UpstreamInfo, StatInfo, ImageInfo
        from datetime import datetime
        import os
        import shutil
        
        test_db_path = "test_database.db"
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        db_config = DatabaseConfig(path=test_db_path)
        db = Database(db_config, logger)
        logger.info("   ✅ 数据库连接成功")
        
        upstream = UpstreamInfo(uid="123456", name="测试UP主", face="https://example.com/face.jpg")
        db.save_upstream(upstream)
        logger.info("   ✅ UP主信息保存成功")
        
        loaded_upstream = db.get_upstream("123456")
        logger.info(f"   ✅ UP主信息读取成功: {loaded_upstream.name}")
        
        stat = StatInfo(like=100, repost=20, comment=30)
        image = ImageInfo(url="https://example.com/image.jpg", width=800, height=600)
        dynamic = DynamicInfo(
            dynamic_id="987654321",
            uid="123456",
            upstream_name="测试UP主",
            dynamic_type="图文",
            content="测试动态内容",
            publish_time=datetime.now(),
            images=[image],
            stat=stat
        )
        
        if db.save_dynamic(dynamic):
            logger.info("   ✅ 动态保存成功")
        
        processed_ids = db.get_processed_ids("123456")
        logger.info(f"   ✅ 已处理动态ID获取成功: {len(processed_ids)}条")
        
        stats = db.get_stats()
        logger.info(f"   ✅ 统计信息获取成功: {stats}")
        
        dynamics = db.get_dynamics(limit=10)
        logger.info(f"   ✅ 动态列表获取成功: {len(dynamics)}条")
        
        db.close()
        logger.info("   ✅ 数据库关闭成功")
        
        if os.path.exists(test_db_path):
            os.remove(test_db_path)
        
        logger.info("✅ 数据库模块测试成功")
        return True
    except Exception as e:
        logger.error(f"❌ 数据库模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        if os.path.exists("test_database.db"):
            try:
                os.remove("test_database.db")
            except:
                pass
        return False

def test_notification_base():
    """测试通知基础模块"""
    logger.info("\n" + "="*50)
    logger.info("测试 5: 通知基础模块 (base.py)")
    logger.info("="*50)
    
    try:
        from bili_monitor.notification.base import NotificationBase, NotificationResult
        from bili_monitor.core.models import DynamicInfo, StatInfo
        from datetime import datetime
        
        class TestNotifier(NotificationBase):
            def send(self, dynamic):
                return NotificationResult(success=True, message="测试成功")
            
            def test(self):
                return True
        
        notifier = TestNotifier(logger)
        logger.info("   ✅ 通知器基类初始化成功")
        
        dynamic = DynamicInfo(
            dynamic_id="123456",
            uid="123456",
            upstream_name="测试UP主",
            dynamic_type="图文",
            content="测试内容",
            publish_time=datetime.now(),
            stat=StatInfo()
        )
        
        result = notifier.send(dynamic)
        logger.info(f"   ✅ 通知发送测试: {result.message}")
        
        test_result = notifier.test()
        logger.info(f"   ✅ 通知器测试: {'成功' if test_result else '失败'}")
        
        formatted_msg = notifier.format_message(dynamic)
        logger.info(f"   ✅ 消息格式化成功，长度: {len(formatted_msg)}")
        
        simple_msg = notifier.format_simple_message(dynamic)
        logger.info(f"   ✅ 简化消息格式化成功，长度: {len(simple_msg)}")
        
        logger.info("✅ 通知基础模块测试成功")
        return True
    except Exception as e:
        logger.error(f"❌ 通知基础模块测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_bili_api_basic():
    """测试B站API基础功能"""
    logger.info("\n" + "="*50)
    logger.info("测试 6: B站API基础功能 (bili_api.py)")
    logger.info("="*50)
    
    try:
        from bili_monitor.api.bili_api import BiliAPI
        
        api = BiliAPI(logger=logger)
        logger.info("   ✅ BiliAPI 初始化成功")
        
        logger.info("   📝 测试获取用户信息...")
        try:
            user_info = api.get_user_info("546195")
            if user_info and user_info.name:
                logger.info(f"   ✅ 用户信息获取成功: {user_info.name}")
            else:
                logger.warning("   ⚠️ 用户信息获取返回空（可能需要Cookie）")
        except Exception as e:
            logger.warning(f"   ⚠️ 用户信息获取失败（可能需要Cookie）: {e}")
        
        logger.info("   📝 测试获取粉丝数...")
        try:
            fans = api.get_user_fans("546195")
            logger.info(f"   ✅ 粉丝数获取: {fans}")
        except Exception as e:
            logger.warning(f"   ⚠️ 粉丝数获取失败: {e}")
        
        api.close()
        logger.info("   ✅ API连接关闭成功")
        
        logger.info("✅ B站API基础功能测试完成")
        return True
    except Exception as e:
        logger.error(f"❌ B站API基础功能测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    logger.info("="*50)
    logger.info("B站UP主动态监控系统 - 全面功能测试")
    logger.info("="*50)
    logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    results = {}
    
    results["配置模块"] = test_config()
    results["日志模块"] = test_logger()
    results["数据模型"] = test_models()
    results["数据库模块"] = test_database()
    results["通知基础模块"] = test_notification_base()
    results["B站API基础"] = test_bili_api_basic()
    
    logger.info("\n" + "="*50)
    logger.info("测试结果汇总")
    logger.info("="*50)
    
    passed = 0
    failed = 0
    
    for name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        logger.info(f"{name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info("\n" + "-"*50)
    logger.info(f"总计: {len(results)} 个测试")
    logger.info(f"通过: {passed} 个")
    logger.info(f"失败: {failed} 个")
    logger.info(f"完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if failed == 0:
        logger.info("\n🎉 所有测试通过！")
        return 0
    else:
        logger.warning(f"\n⚠️ 有 {failed} 个测试失败")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
