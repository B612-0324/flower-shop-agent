"""市场 Agent（v2.0 新增）：
- 监控高价值客户（累计消费 TOP）
- 节假日触发促销事件（这里用"第 N 天"模拟）
- 给销售 Agent 一个"主动营销"建议事件
"""
import random
from core.enums import EventType
from core.message_bus import Message
from agents.base_agent import BaseAgent


class MarketingAgent(BaseAgent):
    name = "市场Agent"

    def setup(self):
        self.bus.subscribe(EventType.DAILY_REPORT_REQUEST, self._on_daily)

    def _on_daily(self, msg: Message):
        # 找累计消费最高的客户
        if not self.state.orders:
            return
        top = max((c for c in self._customers()), key=lambda c: c.total_spent, default=None)
        if top and top.total_spent > 0:
            self.log.info(f"VIP 提醒：{top.name} 累计消费 {top.total_spent:.0f} 元，"
                          f"建议回访")
        # 每 3 天一次随机促销
        if self.state.day % 3 == 0 and random.random() < 0.5:
            self.log.info("今日促销：满 200 减 20，已同步给销售 Agent")

    def _customers(self):
        seen = {}
        for o in self.state.orders.values():
            seen[o.customer.name] = o.customer
        return seen.values()
