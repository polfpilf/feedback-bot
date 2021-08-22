from typing import List, Protocol

from .events import BaseEvent


class BaseAggregate(Protocol):
    events: List[BaseEvent]

    def __init__(self):
        self.events = []
