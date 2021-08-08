from abc import abstractmethod, ABC
from typing import Optional, List

from feedback_bot.model.admin import Admin


class AbstractAdminRepository(ABC):
    @abstractmethod
    def get(self, user_id: int) -> Optional[Admin]:
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> List[Admin]:
        raise NotImplementedError

    @abstractmethod
    def add(self, admin: Admin):
        raise NotImplementedError


class InMemoryAdminRepository(AbstractAdminRepository):
    def __init__(self):
        self.admins = set()
    
    def get(self, user_id: int):
        return next(
            filter(
                lambda admin: admin.user_id == user_id,
                self.admins
            ),
            None,
        )

    def get_all(self):
        return list(self.admins)
    
    def add(self, admin: Admin):
        self.admins.add(admin)