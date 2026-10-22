"""旧构造参数兼容层；全部业务由src实现。"""
from flower_shop.core.state import ShopState as _ShopState
from flower_shop.core.models import FlowerItem as _FlowerItem, Customer, Order
from flower_shop.services.config_loader import load_config


class FlowerItem(_FlowerItem):
    def __init__(self, ftype, unit_price, stock, safety_stock, cost_price, shelf_life=5):
        super().__init__(ftype, unit_price, cost_price, stock, safety_stock, shelf_life)


class ShopState(_ShopState):
    def __init__(self, config=None):
        super().__init__(config if config is not None else load_config())
