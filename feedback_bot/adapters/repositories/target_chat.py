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


class InMemoryTargetChatRepository(AbstractTargetChatRepository):
    def __init__(self, target_chats: Dict[int, TargetChat]):
        self._target_chats = target_chats

    async def get_latest(self):
        return max(
            self._target_chats.values(),
            key=lambda group: group.created_at,
            default=None,
        )
    
    async def remove(self, chat_id: int):
        return self._target_chats.pop(chat_id, None)
    
    async def add(self, target_chat: TargetChat):
        self._target_chats[target_chat.chat_id] = target_chat
