"""测试公共夹具。"""
from __future__ import annotations

import sys
from pathlib import Path

# 把 src 加入 path，便于 pytest 直接跑
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
