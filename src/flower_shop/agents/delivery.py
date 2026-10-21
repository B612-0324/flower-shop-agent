"""配送 Agent：上门/自提，收款。"""
from __future__ import annotations

from ..core.enums import EventType, OrderStatus
from ..core.events import Message, MessageBus
from ..core.state import ShopState
from .base import BaseAgent


class DeliveryAgent(BaseAgent):
    name = "配送Agent"

    def setup(self) -> None:
        self.bus.subscribe(EventType.DELIVERY_REQUEST, self._on_deliver)

    def _on_deliver(self, msg: Message) -> None:
        order = self.state.get_order(msg.payload["order_id"])
        if order is None:
            return
        if order.is_delivery:
            order.status = OrderStatus.DELIVERING
            self.log.info("订单 %s 骑手取件，送往 %s", order.order_id, order.customer.name)
        else:
            self.log.info("订单 %s 到店自提", order.order_id)
        order.status = OrderStatus.COMPLETED
        self.state.settle_order(order)
        self.log.info("订单 %s 收款 %.2f 元", order.order_id, order.total_price)
