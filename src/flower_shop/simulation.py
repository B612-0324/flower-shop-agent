"""七个规则驱动 Agent 的离线运营模拟。"""
import random
from dataclasses import dataclass, asdict
from pathlib import Path
from .agents import (SalesAgent, ShopManagerAgent, InventoryAgent, PurchasingAgent,
                     FloristAgent, DeliveryAgent, MarketingAgent)
from .core.enums import EventType, FlowerType, OrderStatus
from .core.events import Message, MessageBus
from .core.models import Customer
from .services.report import ReportService


@dataclass
class SimulationResult:
    days: int
    total_orders: int
    completed: int
    refused: int
    revenue: float
    profit: float


class Simulation:
    def __init__(self, state, repo=None, seed=42, output_dir="data"):
        self.state, self.repo, self.seed = state, repo, seed
        self.rng = random.Random(seed)
        self.bus = MessageBus()
        self.report = ReportService(state, output_dir)
        self.started = False
        self.customers = [Customer(f"演示客户{i}", f"DEMO-{i:03}", i % 3)
                          for i in range(1, 9)]
        F = FlowerType
        self.bundles = [
            {F.ROSE: 19, F.EUCALYPTUS: 5, F.BABY_BREATH: 3},
            {F.LILY: 6, F.EUCALYPTUS: 4},
            {F.SUNFLOWER: 5, F.CARNATION: 10, F.BABY_BREATH: 4},
            {F.TULIP: 12, F.EUCALYPTUS: 3},
            {F.CARNATION: 20, F.BABY_BREATH: 5}]
        self.bundles = [b for b in self.bundles if set(b) <= set(state.inventory)]
        self.sales = SalesAgent(self.bus, state)
        self.agents = [self.sales] + [cls(self.bus, state) for cls in
            (ShopManagerAgent, InventoryAgent, PurchasingAgent, FloristAgent,
             DeliveryAgent, MarketingAgent)]

    def _one_day(self, day):
        s = self.state
        s.day = day
        before = (s.revenue, s.total_cost, s.spoilage_loss, s.purchase_spend)
        for _ in range(self.rng.randint(3, 7)):
            customer = self.rng.choice(self.customers)
            self.sales.place_order(customer, self.rng.choice(self.bundles),
                                   note=self.rng.choice(["", "生日", "纪念日"]),
                                   is_delivery=self.rng.random() < .7,
                                   is_urgent=self.rng.random() < .2)
            if self.rng.random() < s.config.vip_repeat_prob[customer.vip_level]:
                self.sales.place_order(customer, self.rng.choice(self.bundles), note="复购")
        self.bus.publish(Message(EventType.DAILY_REPORT_REQUEST, "system", {"day": day}))
        today = [o for o in s.orders.values() if o.day == day]
        metrics = dict(day=day, orders=len(today),
                       completed=sum(o.status == OrderStatus.COMPLETED for o in today),
                       refused=sum(o.status == OrderStatus.REFUSED for o in today),
                       revenue=round(s.revenue-before[0], 2),
                       cost=round(s.total_cost-before[1], 2),
                       profit=round(s.revenue-before[0]-s.total_cost+before[1], 2),
                       spoilage=round(s.spoilage_loss-before[2], 2),
                       purchases=round(s.purchase_spend-before[3], 2), cash=s.cash,
                       inventory={k.value: v.stock for k, v in s.inventory.items()})
        s.daily_metrics.append(metrics)
        s.record_event("", "店长Agent", f"第{day}天日报已生成，营收 {metrics['revenue']:.2f}")
        if self.repo:
            for order in today:
                self.repo.save_order(order)
            self.repo.save_daily(s, metrics)
        print(f"第{day}天：订单{len(today)}，完成{metrics['completed']}，"
              f"营收{metrics['revenue']:.2f}，利润{metrics['profit']:.2f}，现金{s.cash:.2f}")

    def run(self, days=7):
        if type(days) is not int or days <= 0:
            raise ValueError("模拟天数必须为正整数")
        if self.started or self.state.orders or self.state.closed_days:
            raise ValueError("每次运行请创建新的ShopState和Simulation")
        if not self.bundles:
            raise ValueError("配置缺少可用花束所需花材")
        self.started = True
        if self.repo:
            self.repo.start_run(self.seed, days)
        for day in range(1, days+1):
            self._one_day(day)
        s = self.state
        self.report.export_orders_csv()
        return SimulationResult(days, len(s.orders),
                                sum(o.status == OrderStatus.COMPLETED for o in s.orders.values()),
                                sum(o.status == OrderStatus.REFUSED for o in s.orders.values()),
                                s.revenue, s.profit)
