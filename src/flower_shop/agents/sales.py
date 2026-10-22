"""销售 Agent：接单、计价。"""
from __future__ import annotations

import itertools
from typing import Dict

from ..core.enums import EventType, FlowerType
from ..core.events import Message, MessageBus
from ..core.models import Customer, Order
from ..core.state import ShopState
from .base import BaseAgent


class SalesAgent(BaseAgent):
    name = "销售Agent"

    def __init__(self, bus: MessageBus, state: ShopState) -> None:
        self._order_seq = itertools.count(1)
        super().__init__(bus, state)

    def place_order(self, customer: Customer, items: Dict[FlowerType, int],
                    note: str = "", is_delivery: bool = True,
                    is_urgent: bool = False) -> Order:
        if customer.vip_level not in (0, 1, 2) or not customer.name.strip():
            raise ValueError("客户名称或VIP等级无效")
        if not items or any(not isinstance(k, FlowerType) or k not in self.state.inventory
                            or type(v) is not int or v <= 0 for k, v in items.items()):
            raise ValueError("花材必须已配置，数量必须为正整数")
        items = dict(items)
        order_id = f"ORD-{next(self._order_seq):04d}"
        order = Order(
            order_id=order_id, customer=customer, items=items, note=note,
            is_delivery=is_delivery, is_urgent=is_urgent, day=self.state.day,
        )

        cfg = self.state.config
        flower_fee = 0.0
        cost = 0.0
        for ftype, qty in items.items():
            item = self.state.inventory.get(ftype)
            if item is None:
                self.log.warning("未知品类 %s，按 0 元计", ftype.value)
                continue
            flower_fee += item.unit_price * qty
            cost += item.cost_price * qty

        extra = cfg.package_fee
        if is_delivery:
            extra += cfg.delivery_fee
        if is_urgent:
            extra += cfg.urgent_surcharge

        discount = cfg.vip_discount.get(customer.vip_level, 1.0)
        order.total_price = round(flower_fee * discount + extra, 2)
        order.cost = round(cost, 2)

        self.state.add_order(order)
        self.state.record_event(order.order_id, self.name, "创建订单")
        self.log.info(
            "新订单 %s：%s (VIP%d) (花材费 %.1f + 附加 %.1f；花材折扣 %.2f) = %.2f",
            order_id, customer.name, customer.vip_level,
            flower_fee, extra, discount, order.total_price,
        )
        self.bus.publish(Message(
            EventType.ORDER_RECEIVED, self.name, {"order_id": order_id},
        ))
        return order
