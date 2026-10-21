"""Agent 基类。"""
from __future__ import annotations

import logging

from ..core.events import MessageBus
from ..core.state import ShopState


class BaseAgent:
    name: str = "BaseAgent"

    def __init__(self, bus: MessageBus, state: ShopState) -> None:
        self.bus = bus
        self.state = state
        self.log = logging.getLogger(f"flower_shop.agent.{self.name}")
        self.setup()

    def setup(self) -> None:
        """子类覆写：订阅事件。"""
