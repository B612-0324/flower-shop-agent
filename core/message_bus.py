from collections import defaultdict, deque
from .enums import EventType


class Message:
    def __init__(self, event_type: EventType, sender: str, payload: dict = None):
        self.event_type = event_type
        self.sender = sender
        self.payload = payload or {}

    def __repr__(self):
        return f"<{self.event_type.value} from={self.sender}>"


class MessageBus:
    def __init__(self):
        self._subscribers = defaultdict(list)
        self.event_log = deque()

    def subscribe(self, event_type: EventType, handler):
        self._subscribers[event_type].append(handler)

    def publish(self, message: Message):
        self.event_log.append(message)
        for handler in self._subscribers.get(message.event_type, []):
            handler(message)
