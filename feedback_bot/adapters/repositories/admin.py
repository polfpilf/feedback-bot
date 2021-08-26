from abc import abstractmethod, ABC
from typing import Iterable, Optional, List, Dict

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
