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
    batches: List[dict] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.freshness <= 0:
            self.freshness = self.shelf_life
        if not self.batches and self.stock:
            self.batches = [{"qty": self.stock, "expires_day": self.shelf_life}]

    def is_low(self) -> bool:
        return self.stock <= self.safety_stock

    def age_one_day(self) -> int:
        """递减各批次剩余保鲜期，并返回过期数量。"""
        for batch in self.batches:
            batch["expires_day"] -= 1
        expired = [batch for batch in self.batches if batch["expires_day"] <= 0]
        spoiled = sum(batch["qty"] for batch in expired)
        self.batches = [batch for batch in self.batches if batch["expires_day"] > 0]
        self.stock -= spoiled
        self.freshness = min((batch["expires_day"] for batch in self.batches), default=0)
        return spoiled

    def deduct(self, qty: int) -> None:
        if type(qty) is not int or qty <= 0 or qty > self.stock:
            raise ValueError("出库数量必须为可用库存内的正整数")
        for batch in sorted(self.batches, key=lambda value: value["expires_day"]):
            used = min(batch["qty"], qty)
            batch["qty"] -= used
            qty -= used
            if qty == 0:
                break
        self.batches = [batch for batch in self.batches if batch["qty"]]
        self.stock = sum(batch["qty"] for batch in self.batches)
        self.freshness = min((batch["expires_day"] for batch in self.batches), default=0)

    def restock(self, qty: int) -> None:
        if type(qty) is not int or qty <= 0:
            raise ValueError("补货数量必须为正整数")
        self.batches.append({"qty": qty, "expires_day": self.shelf_life})
        self.stock += qty
        self.freshness = min(batch["expires_day"] for batch in self.batches)


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
    vip_repeat_prob: Dict[int, float] = field(default_factory=lambda: {0: .05, 1: .2, 2: .35})
