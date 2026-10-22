"""同步发布订阅总线；处理失败显式抛出，避免静默的半完成订单。"""
from collections import defaultdict, deque
from dataclasses import dataclass, field
from .enums import EventType


@dataclass
class Message:
    event_type: EventType
    sender: str
    payload: dict = field(default_factory=dict)


class MessageBus:
    def __init__(self):
        self._subscribers = defaultdict(list)
        self.event_log = deque()

    def subscribe(self, event_type, handler):
        if handler not in self._subscribers[event_type]:
            self._subscribers[event_type].append(handler)

    def publish(self, message):
        self.event_log.append(message)
        for handler in list(self._subscribers.get(message.event_type, [])):
            owner = getattr(handler, "__self__", None)
            if owner is not None and hasattr(owner, "state"):
                owner.state.record_event(message.payload.get("order_id", ""),
                                         owner.name, message.event_type.value)
            handler(message)
