"""SQLite 仓储测试。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from flower_shop.core.enums import FlowerType, OrderStatus
from flower_shop.core.models import Customer, Order
from flower_shop.services.repository import OrderRepository


def test_save_and_list(tmp_path):
    repo = OrderRepository(tmp_path / "test.db")
    order = Order(
        order_id="ORD-TEST", customer=Customer("张三", "138"),
        items={FlowerType.ROSE: 5}, status=OrderStatus.COMPLETED,
        total_price=80.0, cost=20.0, day=1,
    )
    repo.save_order(order)
    rows = repo.list_orders()
    assert len(rows) == 1
    assert rows[0]["order_id"] == "ORD-TEST"
    assert rows[0]["total_price"] == 80.0


def test_snapshot(tmp_path):
    repo = OrderRepository(tmp_path / "test.db")
    from flower_shop.core.models import FlowerItem
    inv = {FlowerType.ROSE: FlowerItem(FlowerType.ROSE, 8, 4, stock=10, safety_stock=5)}
    repo.save_snapshot(day=1, inventory=inv)
    # 重复写同一天不应报错
    repo.save_snapshot(day=1, inventory=inv)
