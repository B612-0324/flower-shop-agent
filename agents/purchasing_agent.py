"""采购 Agent：响应补货预警，按资金约束进货。"""
from core.enums import EventType
from core.message_bus import Message
from agents.base_agent import BaseAgent


class PurchasingAgent(BaseAgent):
    name = "采购Agent"

    def setup(self):
        self.bus.subscribe(EventType.LOW_STOCK_WARNING, self._on_warning)

    def _on_warning(self, msg: Message):
        ftype = msg.payload["flower_type"]
        qty = msg.payload["suggest_qty"]
        item = self.state.inventory[ftype]
        cost = item.cost_price * qty
        reserve = self.state.config["reserve_cash"]
        if self.state.cash - cost < reserve:
            self.log.warning(f"现金不足（余 {self.state.cash:.0f}），{ftype.value} 补货暂缓")
            return
        if self.state.spend(cost):
            item.stock += qty
            item.freshness = item.shelf_life
            self.log.info(f"已采购 {ftype.value} × {qty}，花费 {cost:.2f}，现库存 {item.stock}")
