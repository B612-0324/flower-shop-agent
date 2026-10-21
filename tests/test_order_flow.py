"""端到端：一笔正常订单应走完整个状态机。"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from flower_shop.core.enums import FlowerType, OrderStatus
from flower_shop.core.events import MessageBus
from flower_shop.core.models import Customer, FlowerItem, ShopConfig
from flower_shop.core.state import ShopState
from flower_shop.agents import (
    DeliveryAgent, FloristAgent, InventoryAgent,
    PurchasingAgent, SalesAgent, ShopManagerAgent,
)


def build_state() -> ShopState:
    inv = {
        FlowerType.ROSE: FlowerItem(FlowerType.ROSE, 8.0, 4.0, 60, 20, 5),
        FlowerType.EUCALYPTUS: FlowerItem(FlowerType.EUCALYPTUS, 3.0, 1.2, 40, 15, 10),
    }
    cfg = ShopConfig(
        initial_cash=5000, reserve_cash=1000,
        package_fee=15, delivery_fee=8, urgent_surcharge=20,
        max_auto_price=500, vip_discount={0: 1.0, 1: 0.95, 2: 0.9},
        inventory=inv,
    )
    return ShopState(cfg)


def test_happy_path():
    state = build_state()
    bus = MessageBus()
    sales = SalesAgent(bus, state)
    ShopManagerAgent(bus, state)
    InventoryAgent(bus, state)
    PurchasingAgent(bus, state)
    FloristAgent(bus, state)
    DeliveryAgent(bus, state)

    order = sales.place_order(
        Customer("测试", "138", vip_level=2),
        {FlowerType.ROSE: 10, FlowerType.EUCALYPTUS: 2},
    )
    assert order.status == OrderStatus.COMPLETED
    assert order.total_price > 0
    assert state.revenue == order.total_price
    # 库存被扣减
    assert state.inventory[FlowerType.ROSE].stock == 50


def test_insufficient_stock():
    state = build_state()
    bus = MessageBus()
    sales = SalesAgent(bus, state)
    ShopManagerAgent(bus, state)
    InventoryAgent(bus, state)
    PurchasingAgent(bus, state)
    FloristAgent(bus, state)
    DeliveryAgent(bus, state)

    order = sales.place_order(
        Customer("测试", "138", vip_level=0),
        {FlowerType.ROSE: 999},   # 远超库存
    )
    assert order.status == OrderStatus.REFUSED
    assert order.refuse_reason == "库存不足"
    # 库存不应被扣
    assert state.inventory[FlowerType.ROSE].stock == 60
    # 收入不应增加
    assert state.revenue == 0
