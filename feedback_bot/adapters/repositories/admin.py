from abc import abstractmethod, ABC
from typing import Iterable, Optional, List, Dict

import asyncpg

from feedback_bot.model import Admin, TargetChat


class AbstractAdminRepository(ABC):
    @abstractmethod
    async def get(self, user_id: int) -> Optional[Admin]:
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> List[Admin]:
        raise NotImplementedError

    @abstractmethod
    async def add(self, admin: Admin):
        raise NotImplementedError


class InMemoryAdminRepository(AbstractAdminRepository):
    def __init__(self, admins: Dict[int, Admin], target_chats: Dict[int, TargetChat]):
        self._admins = admins
        self._target_chats = target_chats 
    
    async def get(self, user_id: int):
        return self._admins.get(user_id)

    async def get_all(self):
        return list(self._admins.values())
    
    async def add(self, admin: Admin):
        self._admins[admin.user_id] = admin
        self._target_chats[admin.target_chat.chat_id] = admin.target_chat
