"""库存与报损测试。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from flower_shop.core.enums import FlowerType
from flower_shop.core.models import FlowerItem


def test_freshness_spoilage():
    item = FlowerItem(FlowerType.ROSE, 8.0, 4.0, stock=10, safety_stock=5, shelf_life=2)
    assert item.freshness == 2
    assert item.age_one_day() == 0     # 第 1 天鲜度 1，没坏
    assert item.stock == 10
    assert item.age_one_day() == 10    # 第 2 天鲜度 0，全坏
    assert item.stock == 0


def test_safety_stock():
    item = FlowerItem(FlowerType.ROSE, 8.0, 4.0, stock=5, safety_stock=10)
    assert item.is_low() is True
    item.stock = 20
    assert item.is_low() is False
