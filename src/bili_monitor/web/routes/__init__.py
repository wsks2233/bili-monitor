"""路由模块"""

from .config import config_bp
from .dynamics import dynamics_bp
from .login import login_bp
from .monitor import monitor_bp

__all__ = ["config_bp", "dynamics_bp", "login_bp", "monitor_bp"]
