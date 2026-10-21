"""模拟编排器：把所有 Agent 串起来，跑 N 天。"""
from __future__ import annotations

import logging
import random
from dataclasses import dataclass

from .agents import (
    DeliveryAgent, FloristAgent, InventoryAgent,
    PurchasingAgent, SalesAgent, ShopManagerAgent,
)
from .core.enums import EventType, FlowerType
from .core.events import Message, MessageBus
from .core.models import Customer
from .core.state import ShopState
from .services.report import ReportService
from .services.repository import OrderRepository


@dataclass
class SimulationResult:
    days: int
    total_orders: int
    completed: int
    refused: int
    revenue: float
    profit: float


class Simulation:
    def __init__(self, state: ShopState, repo: OrderRepository | None = None,
                 seed: int = 42) -> None:
        self.state = state
        self.bus = MessageBus()
        self.repo = repo
        self.report = ReportService(state)
        self.log = logging.getLogger("flower_shop.simulation")

        # 客户池 & 花束组合
        self.customers = [
            Customer("张小姐", "138****1001", vip_level=2),
            Customer("李先生", "139****2002", vip_level=1),
            Customer("王女士", "137****3003", vip_level=0),
            Customer("陈先生", "136****4004", vip_level=0),
            Customer("刘女士", "135****5005", vip_level=1),
            Customer("赵先生", "134****6006", vip_level=2),
        ]
        self.bundles = [
            {FlowerType.ROSE: 19, FlowerType.EUCALYPTUS: 5, FlowerType.BABY_BREATH: 3},
            {FlowerType.LILY: 6, FlowerType.EUCALYPTUS: 4},
            {FlowerType.SUNFLOWER: 5, FlowerType.CARNATION: 10, FlowerType.BABY_BREATH: 4},
            {FlowerType.TULIP: 12, FlowerType.EUCALYPTUS: 3},
            {FlowerType.CARNATION: 20, FlowerType.BABY_BREATH: 5},
        ]
        self.rng = random.Random(seed)

        # 装配 Agent
        self.sales = SalesAgent(self.bus, state)
        ShopManagerAgent(self.bus, state)
        InventoryAgent(self.bus, state)
        PurchasingAgent(self.bus, state)
        FloristAgent(self.bus, state)
        DeliveryAgent(self.bus, state)

    def _one_day(self, day: int) -> None:
        self.state.day = day
        n = self.rng.randint(3, 6)
        self.log.info("=== 第 %d 天开始，预计 %d 单 ===", day, n)
        for _ in range(n):
            cust = self.rng.choice(self.customers)
            bundle = self.rng.choice(self.bundles)
            self.sales.place_order(
                cust, bundle,
                note=self.rng.choice(["", "生日", "探望", "教师节", "纪念日"]),
                is_delivery=self.rng.random() < 0.7,
                is_urgent=self.rng.random() < 0.2,
            )
            if self.rng.random() < cust.repeat_prob:
                cust2 = self.rng.choice(self.customers)
                self.sales.place_order(cust2, self.rng.choice(self.bundles),
                                       note="复购", is_delivery=True)

        # 日终
        self.bus.publish(Message(EventType.DAILY_REPORT_REQUEST, "system", {"day": day}))
        if self.repo:
            for o in self.state.list_orders():
                if o.day == day:
                    self.repo.save_order(o)
            self.repo.save_snapshot(day, self.state.inventory)
        print(self.report.daily_report())

    def run(self, days: int = 3) -> SimulationResult:
        for d in range(1, days + 1):
            self._one_day(d)
        done = sum(1 for o in self.state.orders.values() if o.status.value == "COMPLETED")
        refused = sum(1 for o in self.state.orders.values() if o.status.value == "REFUSED")
        self.report.export_orders_csv()
        return SimulationResult(
            days=days,
            total_orders=len(self.state.orders),
            completed=done,
            refused=refused,
            revenue=self.state.revenue,
            profit=self.state.profit,
        )
