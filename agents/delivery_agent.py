"""配送 Agent：上门/自提，收款入账。"""
from core.enums import EventType, OrderStatus
from core.message_bus import Message
from agents.base_agent import BaseAgent


class DeliveryAgent(BaseAgent):
    name = "配送Agent"

    def setup(self):
        self.bus.subscribe(EventType.DELIVERY_REQUEST, self._on_deliver)

    def _on_deliver(self, msg: Message):
        order = self.state.orders[msg.payload["order_id"]]
        if order.is_delivery:
            order.status = OrderStatus.DELIVERING
            self.log.info(f"订单 {order.order_id} 骑手取件，送往 {order.customer.name}")
        else:
            self.log.info(f"订单 {order.order_id} 到店自提")
        order.status = OrderStatus.COMPLETED
        self.state.settle_order(order)
        order.log_event(self.name, f"收款 {order.total_price:.2f} 元，订单完成")
        self.log.info(f"订单 {order.order_id} 完成，收款 {order.total_price:.2f} 元")
