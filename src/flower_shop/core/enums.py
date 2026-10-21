"""枚举定义：订单状态、花材品类、事件类型。"""
from __future__ import annotations

from enum import Enum


class OrderStatus(str, Enum):
    """订单状态机，禁止回退。"""

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    MATERIAL_READY = "MATERIAL_READY"
    MAKING = "MAKING"
    READY = "READY"
    DELIVERING = "DELIVERING"
    COMPLETED = "COMPLETED"
    REFUSED = "REFUSED"

    @property
    def label(self) -> str:
        return {
            "PENDING": "待确认",
            "CONFIRMED": "已确认",
            "MATERIAL_READY": "物料齐备",
            "MAKING": "制作中",
            "READY": "待配送",
            "DELIVERING": "配送中",
            "COMPLETED": "已完成",
            "REFUSED": "已拒绝",
        }[self.value]


class FlowerType(str, Enum):
    ROSE = "ROSE"
    LILY = "LILY"
    CARNATION = "CARNATION"
    TULIP = "TULIP"
    SUNFLOWER = "SUNFLOWER"
    EUCALYPTUS = "EUCALYPTUS"
    BABY_BREATH = "BABY_BREATH"

    @property
    def label(self) -> str:
        return {
            "ROSE": "玫瑰",
            "LILY": "百合",
            "CARNATION": "康乃馨",
            "TULIP": "郁金香",
            "SUNFLOWER": "向日葵",
            "EUCALYPTUS": "尤加利叶",
            "BABY_BREATH": "满天星",
        }[self.value]


class EventType(str, Enum):
    ORDER_RECEIVED = "ORDER_RECEIVED"
    INVENTORY_CHECK_REQUEST = "INVENTORY_CHECK_REQUEST"
    MAKING_REQUEST = "MAKING_REQUEST"
    DELIVERY_REQUEST = "DELIVERY_REQUEST"
    LOW_STOCK_WARNING = "LOW_STOCK_WARNING"
    DAILY_REPORT_REQUEST = "DAILY_REPORT_REQUEST"
