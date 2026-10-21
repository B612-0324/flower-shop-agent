"""销售 Agent：接待客户、计价、创建订单。"""
from core.enums import EventType
from core.message_bus import Message
from core.shop_state import Order, Customer
from agents.base_agent import BaseAgent


class SalesAgent(BaseAgent):
    name = "销售Agent"

    def place_order(self, customer: Customer, items: dict,
                    note="", is_delivery=True, is_urgent=False) -> Order:
        cfg = self.state.config
        order = Order(customer, items, note, is_delivery, is_urgent)

        flower_fee = 0.0
        cost = 0.0
        for ftype, qty in items.items():
            item = self.state.inventory.get(ftype)
            if item is None:
                self.log.warning(f"品类 {ftype.value} 不在价目表")
                continue
            flower_fee += item.unit_price * qty
            cost += item.cost_price * qty

        extra = cfg["package_fee"]
        if is_delivery:
            extra += cfg["delivery_fee"]
        if is_urgent:
            extra += cfg["urgent_surcharge"]

        discount = cfg["vip_discount"].get(str(customer.vip_level), 1.0)
        order.total_price = round(flower_fee * discount + extra, 2)
        order.cost = round(cost, 2)

        self.state.add_order(order)
        order.log_event(self.name, f"创建订单，合计 {order.total_price} 元")
        self.log.info(f"新订单 {order.order_id}：{customer.name}（VIP{customer.vip_level}）"
                      f" {len(items)} 种花材 = {order.total_price} 元")
        self.bus.publish(Message(EventType.ORDER_RECEIVED, self.name,
                                 {"order_id": order.order_id}))
        return order
