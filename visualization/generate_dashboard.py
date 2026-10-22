"""旧仪表盘导入路径兼容层。"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'src'))
from flower_shop.services.dashboard import generate_dashboard
