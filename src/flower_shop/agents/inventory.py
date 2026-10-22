"""库存 Agent：锁料出库、日终盘点、报损、预警。"""
from __future__ import annotations

from ..core.enums import EventType, OrderStatus
from ..core.events import Message, MessageBus
from ..core.state import ShopState
from .base import BaseAgent


class InventoryAgent(BaseAgent):
    name = "库存Agent"

    def setup(self) -> None:
        self.bus.subscribe(EventType.INVENTORY_CHECK_REQUEST, self._on_check)
        self.bus.subscribe(EventType.DAILY_REPORT_REQUEST, self._on_eod)

    def _on_check(self, msg: Message) -> None:
        order = self.state.get_order(msg.payload["order_id"])
        if order is None or order.status != OrderStatus.CONFIRMED:
            return
        if not self.state.check_materials(order.items):
            self.state.transition(order, OrderStatus.CONFIRMED, OrderStatus.REFUSED, self.name)
            order.refuse_reason = "出库前校验失败"
            self.state.refuse_stats["出库前校验失败"] = \
                self.state.refuse_stats.get("出库前校验失败", 0) + 1
            self.log.warning("订单 %s 二次校验失败", order.order_id)
            return
        self.state.deduct_materials(order.items)
        self.state.transition(order, OrderStatus.CONFIRMED, OrderStatus.MATERIAL_READY, self.name)
        self.log.info("订单 %s 物料已出库", order.order_id)
        self.bus.publish(Message(
            EventType.MAKING_REQUEST, self.name, {"order_id": order.order_id},
        ))

    def _on_eod(self, msg: Message) -> None:
        day = msg.payload["day"]
        if day in self.state.closed_days:
            return
        self.state.closed_days.add(day)
        for ftype, item in self.state.inventory.items():
            spoiled = item.age_one_day()
            if spoiled > 0:
                self.state.record_spoilage(ftype, spoiled, item.cost_price)
                self.log.info("%s 鲜度耗尽，报损 %d 枝", ftype.label, spoiled)
            if item.is_low():
                qty = max(item.safety_stock * 2 - item.stock, 30)
                self.log.warning("%s 库存 %d ≤ 安全线 %d，建议补货 %d",
                                 ftype.label, item.stock, item.safety_stock, qty)
                self.bus.publish(Message(
                    EventType.LOW_STOCK_WARNING, self.name,
                    {"flower_type": ftype, "suggest_qty": qty},
                ))
