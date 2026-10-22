"""花艺师 Agent：制作花束。"""
from __future__ import annotations

import time

from ..core.enums import EventType, OrderStatus
from ..core.events import Message, MessageBus
from ..core.state import ShopState
from .base import BaseAgent


class FloristAgent(BaseAgent):
    name = "花艺师Agent"

    def setup(self) -> None:
        self.bus.subscribe(EventType.MAKING_REQUEST, self._on_make)

    def _on_make(self, msg: Message) -> None:
        order = self.state.get_order(msg.payload["order_id"])
        if order is None or order.status != OrderStatus.MATERIAL_READY:
            return
        self.state.transition(order, OrderStatus.MATERIAL_READY, OrderStatus.MAKING, self.name)
        n = sum(order.items.values())
        speed = 0.03 if order.is_urgent else 0.05
        self.state.record_event(order.order_id, self.name,
                                f"制作预计 {speed * n:.2f} 模拟分钟")
        self.state.transition(order, OrderStatus.MAKING, OrderStatus.READY, self.name)
        self.log.info("订单 %s 制作完成（%d 枝%s）",
                      order.order_id, n, "，加急" if order.is_urgent else "")
        self.bus.publish(Message(
            EventType.DELIVERY_REQUEST, self.name, {"order_id": order.order_id},
        ))
