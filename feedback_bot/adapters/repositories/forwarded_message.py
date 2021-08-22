from abc import ABC, abstractmethod
from typing import Iterable, Optional

from feedback_bot.domain.model import ForwardedMessage


class AbstractForwardedMessageRepository(ABC):
    @abstractmethod
    async def get(
        self, forwarded_message_id: int, destination_chat_id: int
    ) -> Optional[ForwardedMessage]:
        raise NotImplementedError

    @abstractmethod
    async def add_many(self, forwarded_messages: Iterable[ForwardedMessage]):
        raise NotImplementedError


class InMemoryForwardedMessageRepository(AbstractForwardedMessageRepository):
    def __init__(self, forwarded_messages: Optional[Iterable[ForwardedMessage]] = None):
        self.forwarded_messages = set(forwarded_messages or ())

    async def get(self, forwarded_message_id: int, destination_chat_id: int):
        return next(
            filter(
                lambda msg: (
                    msg.forwarded_message_id == forwarded_message_id
                    and msg.destination_chat_id == destination_chat_id
                ),
                self.forwarded_messages,
            ),
            None,
        )

    async def add_many(self, forwarded_messages: Iterable[ForwardedMessage]):
        self.forwarded_messages.update(forwarded_messages)
