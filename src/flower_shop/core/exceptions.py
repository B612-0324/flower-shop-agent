"""自定义异常。"""


class ShopError(Exception):
    """业务异常基类。"""


class InsufficientStockError(ShopError):
    """库存不足。"""


class InsufficientCashError(ShopError):
    """现金不足。"""


class OrderNotFoundError(ShopError):
    """订单不存在。"""


class InvalidConfigError(ShopError):
    """配置文件非法。"""
