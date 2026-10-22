"""每次模拟独立的共享黑板及账务。"""
from copy import deepcopy
from .enums import FlowerType, OrderStatus
from .models import Order, ShopConfig


class ShopState:
    def __init__(self, config: ShopConfig):
        self.config = deepcopy(config)
        self.inventory = deepcopy(config.inventory)
        self.orders = {}
        self.cash = config.initial_cash
        self.revenue = self.total_cost = self.spoilage_loss = self.purchase_spend = 0.0
        self.refuse_stats = {}
        self.day = 1
        self.timeline = []
        self.daily_metrics = []
        self.closed_days = set()
        self.purchase_keys = set()
        self.settled = set()

    def record_event(self, order_id, agent, action):
        self.timeline.append(dict(seq=len(self.timeline)+1, day=self.day,
                                  order_id=order_id, agent=agent, action=action))

    def transition(self, order, expected, target, agent):
        if order.status != expected:
            return False
        allowed = {
            OrderStatus.PENDING: {OrderStatus.CONFIRMED, OrderStatus.REFUSED},
            OrderStatus.CONFIRMED: {OrderStatus.MATERIAL_READY, OrderStatus.REFUSED},
            OrderStatus.MATERIAL_READY: {OrderStatus.MAKING},
            OrderStatus.MAKING: {OrderStatus.READY},
            OrderStatus.READY: {OrderStatus.DELIVERING, OrderStatus.COMPLETED},
            OrderStatus.DELIVERING: {OrderStatus.COMPLETED},
        }
        if target not in allowed.get(expected, set()):
            raise ValueError("非法订单状态转换")
        order.status = target
        self.record_event(order.order_id, agent, target.value)
        return True

    def check_materials(self, items):
        return bool(items) and all(k in self.inventory and type(v) is int and v > 0
                                   and self.inventory[k].stock >= v for k, v in items.items())

    def deduct_materials(self, items):
        if not self.check_materials(items):
            raise ValueError("库存不足或数量无效")
        for flower, qty in items.items():
            self.inventory[flower].deduct(qty)

    def add_order(self, order):
        if order.order_id in self.orders:
            raise ValueError("订单编号重复")
        self.orders[order.order_id] = order

    def get_order(self, order_id):
        return self.orders.get(order_id)

    def settle_order(self, order):
        if order.status != OrderStatus.COMPLETED or order.order_id in self.settled:
            return
        self.settled.add(order.order_id)
        self.revenue = round(self.revenue + order.total_price, 2)
        self.total_cost = round(self.total_cost + order.cost, 2)
        self.cash = round(self.cash + order.total_price, 2)

    def spend(self, amount):
        if amount < 0:
            raise ValueError("采购金额不可为负")
        if self.cash - amount < self.config.reserve_cash:
            return False
        self.cash = round(self.cash - amount, 2)
        self.purchase_spend = round(self.purchase_spend + amount, 2)
        return True

    def record_spoilage(self, flower, qty, unit_cost):
        loss = round(qty * unit_cost, 2)
        self.spoilage_loss = round(self.spoilage_loss + loss, 2)
        self.total_cost = round(self.total_cost + loss, 2)

    @property
    def profit(self):
        return round(self.revenue - self.total_cost, 2)

    def list_orders(self):
        return list(self.orders.values())
