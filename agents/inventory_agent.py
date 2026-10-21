"""库存 Agent：锁料出库、花材报损、低库存预警。"""
from core.enums import EventType, OrderStatus
from core.message_bus import Message
from agents.base_agent import BaseAgent


class InventoryAgent(BaseAgent):
    name = "库存Agent"

    def setup(self):
        self.bus.subscribe(EventType.INVENTORY_CHECK_REQUEST, self._on_check)
        self.bus.subscribe(EventType.DAILY_REPORT_REQUEST, self._on_eod)

    def _on_check(self, msg: Message):
        order = self.state.orders[msg.payload["order_id"]]
        if not self.state.check_materials(order.items):
            order.status = OrderStatus.REFUSED
            order.refuse_reason = "出库前校验失败"
            self.state.add_refuse("出库前校验失败")
            order.log_event(self.name, "拒绝：出库前校验失败")
            return
        self.state.deduct_materials(order.items)
        order.status = OrderStatus.MATERIAL_READY
        order.log_event(self.name, "物料已出库")
        self.log.info(f"订单 {order.order_id} 物料已出库")
        self.bus.publish(Message(EventType.MAKING_REQUEST, self.name,
                                 {"order_id": order.order_id}))

    def _on_eod(self, msg: Message):
        for ftype, item in self.state.inventory.items():
            spoiled = item.age_one_day()
            if spoiled > 0:
                self.state.record_spoilage(ftype, spoiled, item.cost_price)
                self.log.info(f"✗ {ftype.value} 报损 {spoiled} 枝")
            if item.is_low():
                qty = max(item.safety_stock * 2 - item.stock, 30)
                self.log.info(f"⚠ {ftype.value} 库存 {item.stock} ≤ 安全线 {item.safety_stock}，建议补 {qty} 枝")
                self.bus.publish(Message(EventType.LOW_STOCK_WARNING, self.name,
                                         {"flower_type": ftype, "suggest_qty": qty}))
