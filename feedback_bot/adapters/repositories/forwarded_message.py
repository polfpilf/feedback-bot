from abc import ABC, abstractmethod
from typing import Dict, Iterable, Optional, Tuple

from feedback_bot.model import ForwardedMessage


class AbstractForwardedMessageRepository(ABC):
    @abstractmethod
    async def get(
        self, forwarded_message_id: int, target_chat_id: int
    ) -> Optional[ForwardedMessage]:
        raise NotImplementedError

    @abstractmethod
    async def add(self, forwarded_message: ForwardedMessage):
        raise NotImplementedError


class InMemoryForwardedMessageRepository(AbstractForwardedMessageRepository):
    def __init__(self, forwarded_messages: Dict[Tuple[int, int], ForwardedMessage]):
        self._forwarded_messages = forwarded_messages

    async def get(self, forwarded_message_id: int, target_chat_id: int):
        key = (forwarded_message_id, target_chat_id)
        return self._forwarded_messages.get(key)

    async def add(self, forwarded_message: ForwardedMessage):
        key = (forwarded_message.forwarded_message_id, forwarded_message.target_chat_id)
        self._forwarded_messages[key] = forwarded_message
