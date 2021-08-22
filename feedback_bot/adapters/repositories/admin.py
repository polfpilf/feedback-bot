from abc import abstractmethod, ABC
from typing import Iterable, Optional, List

from feedback_bot.domain.model import Admin


class AbstractAdminRepository(ABC):
    @abstractmethod
    async def get(self, user_id: int) -> Optional[Admin]:
        raise NotImplementedError

    @abstractmethod
    async def get_latest(self) -> Optional[Admin]:
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> List[Admin]:
        raise NotImplementedError

    @abstractmethod
    async def add(self, admin: Admin):
        raise NotImplementedError


class InMemoryAdminRepository(AbstractAdminRepository):
    def __init__(self, admins: Optional[Iterable[Admin]] = None):
        self.admins = set(admins or ())
    
    async def get(self, user_id: int):
        return next(
            filter(
                lambda admin: admin.user_id == user_id,
                self.admins
            ),
            None,
        )

    async def get_latest(self):
        return max(
            *self.admins,
            key=lambda admin: admin.created_at,
            default=None,
        )

    async def get_all(self):
        return list(self.admins)
    
    async def add(self, admin: Admin):
        self.admins.add(admin)