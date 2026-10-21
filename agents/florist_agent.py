"""花艺师 Agent：制作花束。加急单更快。"""
import time
from core.enums import EventType, OrderStatus
from core.message_bus import Message
from agents.base_agent import BaseAgent


class FloristAgent(BaseAgent):
    name = "花艺师Agent"

    def setup(self):
        self.bus.subscribe(EventType.MAKING_REQUEST, self._on_make)

    def _on_make(self, msg: Message):
        order = self.state.orders[msg.payload["order_id"]]
        order.status = OrderStatus.MAKING
        n = sum(order.items.values())
        speed = 0.03 if order.is_urgent else 0.05
        time.sleep(speed * n)
        order.status = OrderStatus.READY
        tag = "（加急）" if order.is_urgent else ""
        order.log_event(self.name, f"花束制作完成{tag}（{n} 枝）")
        self.log.info(f"订单 {order.order_id} 制作完成{tag}（{n} 枝）")
        self.bus.publish(Message(EventType.DELIVERY_REQUEST, self.name,
                                 {"order_id": order.order_id}))
