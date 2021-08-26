from abc import ABC, abstractmethod
from typing import Dict, Iterable, Optional

from feedback_bot.model import TargetChat


class AbstractTargetChatRepository(ABC):
    @abstractmethod
    async def get_latest(self) -> Optional[TargetChat]:
        raise NotImplementedError

    @abstractmethod
    async def remove(self, chat_id: int) -> Optional[TargetChat]:
        raise NotImplementedError

    @abstractmethod
    async def add(self, target_chat: TargetChat):
        raise NotImplementedError
