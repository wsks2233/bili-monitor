"""测试配置"""

from __future__ import annotations

import sys
from pathlib import Path

# 添加 src 到 Python 路径
src_dir = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_dir))
