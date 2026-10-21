from enum import Enum


class OrderStatus(Enum):
    PENDING       = "待确认"
    CONFIRMED     = "已确认"
    MATERIAL_READY= "物料齐备"
    MAKING        = "制作中"
    READY         = "待配送"
    DELIVERING    = "配送中"
    COMPLETED     = "已完成"
    REFUSED       = "已拒绝"


class FlowerType(Enum):
    ROSE        = "玫瑰"
    LILY        = "百合"
    CARNATION   = "康乃馨"
    TULIP       = "郁金香"
    SUNFLOWER   = "向日葵"
    EUCALYPTUS  = "尤加利叶"
    BABY_BREATH = "满天星"


class EventType(Enum):
    ORDER_RECEIVED          = "ORDER_RECEIVED"
    INVENTORY_CHECK_REQUEST = "INVENTORY_CHECK_REQUEST"
    MAKING_REQUEST          = "MAKING_REQUEST"
    DELIVERY_REQUEST        = "DELIVERY_REQUEST"
    LOW_STOCK_WARNING       = "LOW_STOCK_WARNING"
    DAILY_REPORT_REQUEST    = "DAILY_REPORT_REQUEST"
    SPOILAGE_REPORT         = "SPOILAGE_REPORT"
