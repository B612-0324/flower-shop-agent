"""店长 Agent：审批订单、出日报。"""
from core.enums import EventType, OrderStatus
from core.message_bus import Message
from agents.base_agent import BaseAgent


class ShopManagerAgent(BaseAgent):
    name = "店长Agent"

    def setup(self):
        self.bus.subscribe(EventType.ORDER_RECEIVED, self._on_order)
        self.bus.subscribe(EventType.DAILY_REPORT_REQUEST, self._on_report)

    def _on_order(self, msg: Message):
        order = self.state.orders[msg.payload["order_id"]]
        if not self.state.check_materials(order.items):
            order.status = OrderStatus.REFUSED
            order.refuse_reason = "库存不足"
            self.state.add_refuse("库存不足")
            order.log_event(self.name, "拒绝：库存不足")
            self.log.info(f"订单 {order.order_id} 拒绝：库存不足")
            return
        order.status = OrderStatus.CONFIRMED
        max_price = self.state.config["max_auto_price"]
        if order.total_price <= max_price:
            order.log_event(self.name, f"自动放行（{order.total_price} ≤ {max_price}）")
            self.log.info(f"订单 {order.order_id} 自动放行")
        else:
            order.log_event(self.name, f"店长特批（{order.total_price} > {max_price}）")
            self.log.info(f"订单 {order.order_id} 金额 {order.total_price}，特批通过")
        self.bus.publish(Message(EventType.INVENTORY_CHECK_REQUEST, self.name,
                                 {"order_id": order.order_id}))

    def _on_report(self, msg: Message):
        s = self.state
        profit = s.profit
        margin = (profit / s.revenue * 100) if s.revenue > 0 else 0
        done = sum(1 for o in s.orders.values() if o.status == OrderStatus.COMPLETED)
        refused = sum(1 for o in s.orders.values() if o.status == OrderStatus.REFUSED)
        self.log.info(f"第{s.day}日：营收{s.revenue:.2f} 成本{s.total_cost:.2f} "
                      f"利润{profit:.2f}({margin:.1f}%) 订单{len(s.orders)}(完成{done}/拒{refused})")
