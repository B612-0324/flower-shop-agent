"""冒烟测试：跑 1 天模拟，确认不崩"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.message_bus import MessageBus
from core.shop_state import ShopState, FlowerItem, Customer
from core.enums import FlowerType, EventType
from agents import (SalesAgent, ShopManagerAgent, InventoryAgent,
                    PurchasingAgent, FloristAgent, DeliveryAgent)


def test_smoke():
    bus = MessageBus()
    state = ShopState()
    state.inventory = {
        FlowerType.ROSE: FlowerItem(FlowerType.ROSE, 8.0, 60, 20, 4.0),
    }
    sales = SalesAgent(bus, state)
    ShopManagerAgent(bus, state)
    InventoryAgent(bus, state)
    PurchasingAgent(bus, state)
    FloristAgent(bus, state)
    DeliveryAgent(bus, state)

    order = sales.place_order(Customer("测试", "123", 0), {FlowerType.ROSE: 10})
    assert order.total_price > 0
    assert state.revenue > 0
    print("PASS: 冒烟测试通过")


if __name__ == "__main__":
    test_smoke()
