"""规则驱动的客户回访建议，不调用外部模型。"""
from collections import defaultdict
from .base import BaseAgent
from ..core.enums import EventType, OrderStatus


class MarketingAgent(BaseAgent):
    name = "市场Agent"

    def setup(self):
        self.days = set()
        self.bus.subscribe(EventType.DAILY_REPORT_REQUEST, self._on_daily)

    def _on_daily(self, message):
        if self.state.day in self.days:
            return
        self.days.add(self.state.day)
        spending = defaultdict(float)
        for order in self.state.orders.values():
            if order.status == OrderStatus.COMPLETED:
                spending[order.customer.name] += order.total_price
        if spending:
            name = max(spending, key=spending.get)
            self.state.record_event("", self.name,
                                    f"建议回访 {name}，累计消费 {spending[name]:.2f}")
