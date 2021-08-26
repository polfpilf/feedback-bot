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
