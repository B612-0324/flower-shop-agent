"""采购 Agent：响应补货预警。"""
from __future__ import annotations

from ..core.enums import EventType
from ..core.events import Message, MessageBus
from ..core.state import ShopState
from .base import BaseAgent


class PurchasingAgent(BaseAgent):
    name = "采购Agent"

    def setup(self) -> None:
        self.bus.subscribe(EventType.LOW_STOCK_WARNING, self._on_warning)

    def _on_warning(self, msg: Message) -> None:
        ftype = msg.payload["flower_type"]
        qty = msg.payload["suggest_qty"]
        key = (self.state.day, ftype)
        if key in self.state.purchase_keys:
            return
        if type(qty) is not int or qty <= 0:
            raise ValueError("采购数量必须为正整数")
        self.state.purchase_keys.add(key)
        item = self.state.inventory[ftype]
        cost = item.cost_price * qty
        if not self.state.spend(cost):
            self.log.warning("现金不足，%s 补货 %.2f 元被暂缓", ftype.label, cost)
            return
        item.restock(qty)
        self.state.record_event("", self.name, f"采购 {ftype.value} × {qty}，现金支出 {cost:.2f}")
        self.log.info("已采购 %s × %d 枝，花费 %.2f", ftype.label, qty, cost)
