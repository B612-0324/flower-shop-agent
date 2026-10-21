"""Agent 基类：统一日志接口与总线/状态引用。"""
import logging
from core.message_bus import MessageBus
from core.shop_state import ShopState


class BaseAgent:
    name = "BaseAgent"

    def __init__(self, bus: MessageBus, state: ShopState):
        self.bus = bus
        self.state = state
        self.log = logging.getLogger(self.name)
        self.setup()

    def setup(self):
        pass
