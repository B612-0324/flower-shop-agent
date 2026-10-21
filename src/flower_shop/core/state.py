"""共享黑板：所有 Agent 读写同一份状态。"""
from __future__ import annotations

from typing import Dict, List

from .enums import FlowerType, OrderStatus
from .models import FlowerItem, Order, ShopConfig


class ShopState:
    def __init__(self, config: ShopConfig) -> None:
        self.config = config
        self.inventory: Dict[FlowerType, FlowerItem] = dict(config.inventory)
        self.orders: Dict[str, Order] = {}
        self.cash: float = config.initial_cash
        self.revenue: float = 0.0
        self.total_cost: float = 0.0
        self.spoilage_loss: float = 0.0
        self.refuse_stats: Dict[str, int] = {}
        self.day: int = 1

    # ---------- 库存 ----------
    def check_materials(self, items: Dict[FlowerType, int]) -> bool:
        for ftype, need in items.items():
            if ftype not in self.inventory or self.inventory[ftype].stock < need:
                return False
        return True

    def deduct_materials(self, items: Dict[FlowerType, int]) -> None:
        for ftype, need in items.items():
            self.inventory[ftype].stock -= need

    # ---------- 订单 ----------
    def add_order(self, order: Order) -> None:
        self.orders[order.order_id] = order

    def get_order(self, order_id: str) -> Order | None:
        return self.orders.get(order_id)

    # ---------- 账务 ----------
    def settle_order(self, order: Order) -> None:
        self.revenue += order.total_price
        self.total_cost += order.cost
        self.cash += order.total_price

    def spend(self, amount: float) -> bool:
        if self.cash - amount < self.config.reserve_cash:
            return False
        self.cash -= amount
        self.total_cost += amount
        return True

    def record_spoilage(self, ftype: FlowerType, qty: int, unit_cost: float) -> None:
        loss = qty * unit_cost
        self.spoilage_loss += loss
        self.total_cost += loss

    @property
    def profit(self) -> float:
        return self.revenue - self.total_cost

    def list_orders(self) -> List[Order]:
        return list(self.orders.values())
