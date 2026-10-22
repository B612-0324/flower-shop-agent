"""源码检出兼容入口；与安装后的 flower-shop 使用同一实现。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / 'src'))
from flower_shop.cli import main

if __name__ == '__main__':
    raise SystemExit(main())
