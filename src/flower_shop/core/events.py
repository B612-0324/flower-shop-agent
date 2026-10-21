"""事件总线：发布-订阅。"""
from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Callable, Deque, Dict, List, Any

from .enums import EventType


@dataclass
class Message:
    event_type: EventType
    sender: str
    payload: Dict[str, Any] = field(default_factory=dict)


Handler = Callable[[Message], None]


class MessageBus:
    """进程内同步消息总线。

    - ``subscribe(event, handler)`` 注册回调
    - ``publish(msg)`` 同步触发所有订阅者，并把消息写入 ``event_log``
    """

    def __init__(self) -> None:
        self._subscribers: Dict[EventType, List[Handler]] = defaultdict(list)
        self.event_log: Deque[Message] = deque()

    def subscribe(self, event_type: EventType, handler: Handler) -> None:
        self._subscribers[event_type].append(handler)

    def publish(self, message: Message) -> None:
        self.event_log.append(message)
        for handler in list(self._subscribers.get(message.event_type, [])):
            try:
                handler(message)
            except Exception as exc:  # noqa: BLE001
                # 一个订阅者出错不应该拖垮整条链，但要留下痕迹
                import logging
                logging.getLogger("flower_shop.bus").exception(
                    "handler %s failed on %s: %s", handler, message.event_type, exc
                )
