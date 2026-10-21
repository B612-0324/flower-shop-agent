"""共享黑板：库存、订单、客户、账务。
v2.0 新增：
  - Order.timeline：记录订单从生到死的完整处理时间线
  - ShopState 从 JSON 配置初始化
"""
import json
import os
from datetime import datetime
from .enums import FlowerType, OrderStatus


class FlowerItem:
    def __init__(self, ftype, unit_price, stock, safety_stock, cost_price, shelf_life=5):
        self.type = ftype
        self.unit_price = unit_price
        self.cost_price = cost_price
        self.stock = stock
        self.safety_stock = safety_stock
        self.freshness = shelf_life
        self.shelf_life = shelf_life

    def is_low(self):
        return self.stock <= self.safety_stock

    def age_one_day(self):
        self.freshness -= 1
        if self.freshness <= 0:
            spoiled = self.stock
            self.stock = 0
            return spoiled
        return 0


class Customer:
    def __init__(self, name, phone, vip_level=0):
        self.name = name
        self.phone = phone
        self.vip_level = vip_level
        self.total_spent = 0.0

    def repeat_prob(self, cfg):
        return cfg["vip_repeat_prob"].get(str(self.vip_level), 0.05)


class Order:
    _seq = 0

    def __init__(self, customer, items, note="", is_delivery=True, is_urgent=False):
        Order._seq += 1
        self.order_id = f"ORD-{Order._seq:04d}"
        self.customer = customer
        self.items = items
        self.note = note
        self.is_delivery = is_delivery
        self.is_urgent = is_urgent
        self.status = OrderStatus.PENDING
        self.total_price = 0.0
        self.cost = 0.0
        self.refuse_reason = ""
        self.timeline = []

    def log_event(self, agent_name, action):
        self.timeline.append((datetime.now().strftime("%H:%M:%S"),
                              agent_name, action))


class ShopState:
    def __init__(self, config=None):
        self.config = config or self._load_default_config()
        self.inventory = {}
        self.orders = {}
        self.cash = self.config["initial_cash"]
        self.revenue = 0.0
        self.total_cost = 0.0
        self.spoilage_loss = 0.0
        self.refuse_stats = {}
        self.day = 1
        self._load_inventory()

    @staticmethod
    def _load_default_config():
        path = os.path.join(os.path.dirname(__file__), "..",
                            "config", "shop_config.json")
        with open(path, encoding="utf-8") as f:
            return json.load(f)

    def _load_inventory(self):
        for type_name, info in self.config["inventory"].items():
            ftype = FlowerType[type_name]
            self.inventory[ftype] = FlowerItem(
                ftype, info["unit_price"], info["stock"],
                info["safety_stock"], info["cost_price"],
                info.get("shelf_life", 5),
            )

    def check_materials(self, items):
        for ftype, need in items.items():
            if ftype not in self.inventory or self.inventory[ftype].stock < need:
                return False
        return True

    def deduct_materials(self, items):
        for ftype, need in items.items():
            self.inventory[ftype].stock -= need

    def add_order(self, order):
        self.orders[order.order_id] = order

    def settle_order(self, order):
        self.revenue += order.total_price
        self.total_cost += order.cost
        self.cash += order.total_price
        order.customer.total_spent += order.total_price

    def spend(self, amount):
        if self.cash >= amount:
            self.cash -= amount
            self.total_cost += amount
            return True
        return False

    def record_spoilage(self, ftype, qty, unit_cost):
        loss = qty * unit_cost
        self.spoilage_loss += loss
        self.total_cost += loss

    def add_refuse(self, reason):
        self.refuse_stats[reason] = self.refuse_stats.get(reason, 0) + 1

    @property
    def profit(self):
        return self.revenue - self.total_cost
