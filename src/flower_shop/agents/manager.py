"""店长 Agent：审批订单。"""
from __future__ import annotations

from ..core.enums import EventType, OrderStatus
from ..core.events import Message, MessageBus
from ..core.state import ShopState
from .base import BaseAgent


class ShopManagerAgent(BaseAgent):
    name = "店长Agent"

    def setup(self) -> None:
        self.bus.subscribe(EventType.ORDER_RECEIVED, self._on_order)

    def _on_order(self, msg: Message) -> None:
        order = self.state.get_order(msg.payload["order_id"])
        if order is None:
            self.log.error("订单 %s 不存在", msg.payload["order_id"])
            return

        if not self.state.check_materials(order.items):
            order.status = OrderStatus.REFUSED
            order.refuse_reason = "库存不足"
            self.state.refuse_stats["库存不足"] = \
                self.state.refuse_stats.get("库存不足", 0) + 1
            self.log.info("订单 %s 拒绝：库存不足", order.order_id)
            return

        order.status = OrderStatus.CONFIRMED
        if order.total_price <= self.state.config.max_auto_price:
            self.log.info("订单 %s 自动放行 (%.2f)", order.order_id, order.total_price)
        else:
            self.log.info("订单 %s 金额 %.2f，店长特批通过",
                          order.order_id, order.total_price)

        self.bus.publish(Message(
            EventType.INVENTORY_CHECK_REQUEST, self.name,
            {"order_id": order.order_id},
        ))
