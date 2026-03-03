# -*- coding: utf-8 -*-

import asyncio
import logging
import os
import threading
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..core.config import load_config, Config, MonitorConfig, LoggerConfig, DatabaseConfig, UpstreamConfig
from ..core.logger import setup_logger
from ..monitor import Monitor
from ..api.cookie_service import CookieService, get_cookie_service, check_cookie_status_standalone


class UpstreamModel(BaseModel):
    uid: str
    name: str = ""


class MonitorConfigModel(BaseModel):
    check_interval: int = 300
    retry_times: int = 3
    retry_delay: int = 5
    cookie: str = ""


class LoggerConfigModel(BaseModel):
    level: str = "INFO"
    file: str = "logs/bili-monitor.log"
    max_bytes: int = 10485760
    backup_count: int = 5


class DatabaseConfigModel(BaseModel):
    type: str = "sqlite"
    path: str = "data/bili_monitor.db"
    host: str = "localhost"
    port: int = 3306
    user: str = ""
    password: str = ""
    database: str = "bili_monitor"


class NotificationItemModel(BaseModel):
    type: str
    webhook_url: str = ""
    secret: str = ""
    serverchan_key: str = ""
    pushplus_token: str = ""
    smtp_server: str = ""
    smtp_port: int = 465
    smtp_user: str = ""
    smtp_password: str = ""
    sender: str = ""
    receivers: List[str] = []
    bot_token: str = ""
    chat_id: str = ""


class ConfigModel(BaseModel):
    monitor: MonitorConfigModel
    upstreams: List[UpstreamModel]
    logger: LoggerConfigModel
    database: DatabaseConfigModel
    notification: List[NotificationItemModel] = []


class MonitorStatus(BaseModel):
    running: bool
    uptime: Optional[str] = None
    last_check: Optional[str] = None
    total_dynamics: int = 0
    total_upstreams: int = 0
    cookie_valid: bool = False
    cookie_username: Optional[str] = None


monitor_instance: Optional[Monitor] = None
monitor_thread: Optional[threading.Thread] = None
config_path: str = "config.yaml"
start_time: Optional[datetime] = None
logger: Optional[logging.Logger] = None
cookie_service: Optional[CookieService] = None


def _mask_cookie(cookie: str) -> str:
    if not cookie or len(cookie) < 20:
        return cookie[:5] + '...' if cookie else ''
    return cookie[:10] + '...' + cookie[-5:]


# 使用 cookie_service 中的函数，不再需要本地定义
# _check_cookie_status_standalone 现在从 cookie_service 导入


@asynccontextmanager
async def lifespan(app: FastAPI):
    global logger, cookie_service
    try:
        config = load_config(config_path)
        logger = setup_logger(config.logger)
        
        # 初始化 Cookie 服务
        cookie_service = get_cookie_service(config_path)
        cookie_service.start_keepalive()
        
        logger.info("Web 服务启动")
    except Exception:
        logger = logging.getLogger('bili-monitor.web')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s'))
        logger.addHandler(handler)
        logger.info("Web 服务启动（使用默认日志配置）")
    
    yield
    
    logger.info("Web 服务关闭")
    if cookie_service:
        cookie_service.close()
    if monitor_instance and monitor_instance.running:
        monitor_instance.running = False


app = FastAPI(
    title="B站UP主动态监控系统",
    description="Web管理界面",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/")
async def index():
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return {"message": "B站动态监控API服务运行中"}


@app.get("/api/config", response_model=ConfigModel)
async def get_config():
    try:
        config = load_config(config_path)
        masked_cookie = _mask_cookie(config.monitor.cookie)
        
        notification_list = []
        for n in config.notification:
            notification_list.append(NotificationItemModel(
                type=n.get('type', ''),
                webhook_url=n.get('webhook_url', ''),
                secret=n.get('secret', ''),
                serverchan_key=_mask_cookie(n.get('serverchan_key', '')) if n.get('serverchan_key') else '',
                pushplus_token=_mask_cookie(n.get('pushplus_token', '')) if n.get('pushplus_token') else '',
                smtp_server=n.get('smtp_server', ''),
                smtp_port=n.get('smtp_port', 465),
                smtp_user=n.get('smtp_user', ''),
                smtp_password='******' if n.get('smtp_password') else '',
                sender=n.get('sender', ''),
                receivers=n.get('receivers', []),
                bot_token=_mask_cookie(n.get('bot_token', '')) if n.get('bot_token') else '',
                chat_id=n.get('chat_id', ''),
            ))
        
        return ConfigModel(
            monitor=MonitorConfigModel(
                check_interval=config.monitor.check_interval,
                retry_times=config.monitor.retry_times,
                retry_delay=config.monitor.retry_delay,
                cookie=masked_cookie,
            ),
            upstreams=[UpstreamModel(uid=u.uid, name=u.name) for u in config.upstreams],
            logger=LoggerConfigModel(
                level=config.logger.level,
                file=config.logger.file,
                max_bytes=config.logger.max_bytes,
                backup_count=config.logger.backup_count,
            ),
            database=DatabaseConfigModel(
                type=config.database.type,
                path=config.database.path,
                host=config.database.host,
                port=config.database.port,
                user=config.database.user,
                password='******' if config.database.password else '',
                database=config.database.database,
            ),
            notification=notification_list,
        )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="配置文件不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/config")
async def update_config(config_data: ConfigModel):
    try:
        import yaml
        
        current_config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                current_config = yaml.safe_load(f) or {}
        
        existing_cookie = current_config.get('monitor', {}).get('cookie', '')
        
        new_cookie = existing_cookie
        if config_data.monitor.cookie:
            if not config_data.monitor.cookie.endswith('...'):
                new_cookie = config_data.monitor.cookie
        
        current_config['monitor'] = {
            'check_interval': config_data.monitor.check_interval,
            'retry_times': config_data.monitor.retry_times,
            'retry_delay': config_data.monitor.retry_delay,
            'cookie': new_cookie,
        }
        
        current_config['upstreams'] = [{'uid': u.uid, 'name': u.name} for u in config_data.upstreams]
        
        current_config['logger'] = {
            'level': config_data.logger.level,
            'file': config_data.logger.file,
            'max_bytes': config_data.logger.max_bytes,
            'backup_count': config_data.logger.backup_count,
        }
        
        db_config = {
            'type': config_data.database.type,
            'path': config_data.database.path,
            'host': config_data.database.host,
            'port': config_data.database.port,
            'user': config_data.database.user,
            'database': config_data.database.database,
        }
        if config_data.database.password and config_data.database.password != '******':
            db_config['password'] = config_data.database.password
        elif current_config.get('database', {}).get('password'):
            db_config['password'] = current_config['database']['password']
        current_config['database'] = db_config
        
        notification_list = []
        for n in config_data.notification:
            n_dict = {'type': n.type}
            if n.webhook_url and not n.webhook_url.endswith('...'):
                n_dict['webhook_url'] = n.webhook_url
            if n.secret:
                n_dict['secret'] = n.secret
            if n.serverchan_key and not n.serverchan_key.endswith('...'):
                n_dict['serverchan_key'] = n.serverchan_key
            if n.pushplus_token and not n.pushplus_token.endswith('...'):
                n_dict['pushplus_token'] = n.pushplus_token
            if n.smtp_server:
                n_dict['smtp_server'] = n.smtp_server
                n_dict['smtp_port'] = n.smtp_port
                n_dict['smtp_user'] = n.smtp_user
                if n.smtp_password and n.smtp_password != '******':
                    n_dict['smtp_password'] = n.smtp_password
                n_dict['sender'] = n.sender
                n_dict['receivers'] = n.receivers
            if n.bot_token and not n.bot_token.endswith('...'):
                n_dict['bot_token'] = n.bot_token
                n_dict['chat_id'] = n.chat_id
            notification_list.append(n_dict)
        
        if notification_list:
            current_config['notification'] = notification_list
        
        os.makedirs(os.path.dirname(config_path) if os.path.dirname(config_path) else '.', exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(current_config, f, allow_unicode=True, default_flow_style=False)
        
        global monitor_instance, cookie_service
        if monitor_instance:
            monitor_instance.config = load_config(config_path)
        
        # 更新 cookie_service
        if cookie_service and new_cookie and new_cookie != existing_cookie:
            cookie_service.update_cookie(new_cookie, save_to_config=False)
        
        return {"success": True, "message": "配置已保存"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status", response_model=MonitorStatus)
async def get_status():
    global monitor_instance, start_time, cookie_service
    
    running = monitor_instance is not None and monitor_instance.running
    uptime = None
    if running and start_time:
        delta = datetime.now() - start_time
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        uptime = f"{hours}h {minutes}m {seconds}s"
    
    stats = {}
    cookie_status = {'valid': False, 'username': None}
    
    if monitor_instance:
        try:
            if monitor_instance.db:
                stats = monitor_instance.get_stats()
            if running and monitor_instance.cookie_manager:
                cookie_status = monitor_instance.get_cookie_status()
        except Exception:
            stats = {}
            cookie_status = {'valid': False, 'username': None}
    
    if not cookie_status.get('valid', False):
        try:
            if cookie_service:
                status = cookie_service.check_status()
                cookie_status = {'valid': status.is_valid, 'username': status.username if status.is_valid else None}
            else:
                config = load_config(config_path)
                if config.monitor.cookie:
                    cookie_status = check_cookie_status_standalone(config.monitor.cookie)
        except Exception:
            pass
    
    return MonitorStatus(
        running=running,
        uptime=uptime,
        last_check=datetime.now().isoformat() if running else None,
        total_dynamics=stats.get('total_dynamics', 0),
        total_upstreams=stats.get('total_upstreams', 0),
        cookie_valid=cookie_status.get('valid', False),
        cookie_username=cookie_status.get('username'),
    )


@app.post("/api/start")
async def start_monitor():
    global monitor_instance, monitor_thread, start_time
    
    if monitor_instance and monitor_instance.running:
        raise HTTPException(status_code=400, detail="监控已在运行中")
    
    try:
        config = load_config(config_path)
        log = setup_logger(config.logger)
        monitor_instance = Monitor(config, log)
        start_time = datetime.now()
        
        def run_monitor():
            try:
                monitor_instance.run()
            except Exception as e:
                log.error(f"监控运行错误: {e}")
        
        monitor_thread = threading.Thread(target=run_monitor, daemon=True)
        monitor_thread.start()
        
        return {"success": True, "message": "监控已启动"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/stop")
async def stop_monitor():
    global monitor_instance, start_time
    
    if not monitor_instance or not monitor_instance.running:
        raise HTTPException(status_code=400, detail="监控未在运行")
    
    monitor_instance.running = False
    start_time = None
    
    return {"success": True, "message": "监控已停止"}


@app.get("/api/upstreams")
async def get_upstreams():
    if not monitor_instance or not monitor_instance.db:
        return []
    
    conn = monitor_instance.db.conn
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM upstreams')
    rows = cursor.fetchall()
    
    return [dict(row) for row in rows]


@app.get("/api/dynamics")
async def get_dynamics(uid: str = None, limit: int = 50, offset: int = 0):
    if not monitor_instance or not monitor_instance.db:
        return []
    
    return monitor_instance.get_dynamics(uid, limit, offset)


@app.get("/api/stats")
async def get_stats():
    if not monitor_instance or not monitor_instance.db:
        return {}
    
    return monitor_instance.get_stats()


from .login import BiliLogin

# 使用 cookie_service 替代 BiliLogin
# bili_login: Optional[BiliLogin] = None
current_qrcode_key: Optional[str] = None


@app.get("/api/login/qrcode")
async def get_login_qrcode():
    global cookie_service, current_qrcode_key
    
    try:
        if not cookie_service:
            cookie_service = get_cookie_service(config_path)
        
        qrcode_url, qrcode_key = cookie_service.get_qrcode()
        
        if qrcode_url and qrcode_key:
            current_qrcode_key = qrcode_key
            
            import qrcode
            from io import BytesIO
            import base64
            
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr.add_data(qrcode_url)
            qr.make(fit=True)
            
            img = qr.make_image(fill_color="black", back_color="white")
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode()
            
            return {
                "success": True,
                "qrcode_key": qrcode_key,
                "qrcode_url": qrcode_url,
                "qrcode_image": f"data:image/png;base64,{img_base64}"
            }
        else:
            raise HTTPException(status_code=500, detail="获取二维码失败")
            
    except ImportError:
        return {
            "success": True,
            "qrcode_key": qrcode_key,
            "qrcode_url": qrcode_url,
            "qrcode_image": None,
            "message": "请安装qrcode库: pip install qrcode[pil]"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/login/check")
async def check_login_status(qrcode_key: str):
    global cookie_service, current_qrcode_key
    
    if not cookie_service:
        raise HTTPException(status_code=400, detail="请先获取二维码")
    
    try:
        status = cookie_service.check_login(qrcode_key)
        
        if status.success:
            import yaml
            
            current_config = {}
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    current_config = yaml.safe_load(f) or {}
            
            current_config.setdefault('monitor', {})['cookie'] = status.cookie
            
            os.makedirs(os.path.dirname(config_path) if os.path.dirname(config_path) else '.', exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(current_config, f, allow_unicode=True, default_flow_style=False)
            
            # 更新 cookie_service
            cookie_service.update_cookie(status.cookie, save_to_config=False)
            
            global monitor_instance
            if monitor_instance:
                monitor_instance.config = load_config(config_path)
            
            masked_cookie = _mask_cookie(status.cookie)
            
            return {
                "success": True,
                "status": 0,
                "message": "登录成功，Cookie 已保存",
                "masked_cookie": masked_cookie,
                "username": status.username
            }
        else:
            return {
                "success": False,
                "status": status.status,
                "message": status.message
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/login/cookie")
async def set_cookie_directly(cookie: str):
    try:
        import yaml
        
        current_config = {}
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                current_config = yaml.safe_load(f) or {}
        
        current_config.setdefault('monitor', {})['cookie'] = cookie
        
        os.makedirs(os.path.dirname(config_path) if os.path.dirname(config_path) else '.', exist_ok=True)
        with open(config_path, 'w', encoding='utf-8') as f:
            yaml.dump(current_config, f, allow_unicode=True, default_flow_style=False)
        
        global monitor_instance
        if monitor_instance:
            monitor_instance.config = load_config(config_path)
        
        return {"success": True, "message": "Cookie已保存"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def start_web_server(host: str = "0.0.0.0", port: int = 8000):
    import uvicorn
    uvicorn.run(app, host=host, port=port)
