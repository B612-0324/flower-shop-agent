"""领域模型：库存、客户、订单。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from .enums import FlowerType, OrderStatus


@dataclass
class FlowerItem:
    ftype: FlowerType
    unit_price: float
    cost_price: float
    stock: int
    safety_stock: int
    shelf_life: int = 5
    freshness: int = field(default=0)

    def __post_init__(self) -> None:
        if self.freshness <= 0:
            self.freshness = self.shelf_life

    def is_low(self) -> bool:
        return self.stock <= self.safety_stock

    def age_one_day(self) -> int:
        """过一天鲜度 -1，返回报损数量。"""
        self.freshness -= 1
        if self.freshness <= 0:
            spoiled = self.stock
            self.stock = 0
            return spoiled
        return 0


@dataclass
class Customer:
    name: str
    phone: str
    vip_level: int = 0  # 0/1/2

    @property
    def repeat_prob(self) -> float:
        return {0: 0.05, 1: 0.20, 2: 0.35}[self.vip_level]


@dataclass
class Order:
    order_id: str
    customer: Customer
    items: Dict[FlowerType, int]
    note: str = ""
    is_delivery: bool = True
    is_urgent: bool = False
    status: OrderStatus = OrderStatus.PENDING
    total_price: float = 0.0
    cost: float = 0.0
    refuse_reason: str = ""
    day: int = 1


@dataclass
class ShopConfig:
    """从 config/shop_config.json 加载的配置。"""
    initial_cash: float
    reserve_cash: float           # 采购时保留的周转金
    package_fee: float
    delivery_fee: float
    urgent_surcharge: float
    max_auto_price: float         # 店长自动放行额度
    vip_discount: Dict[int, float]
    inventory: Dict[FlowerType, FlowerItem]
