from abc import ABC, abstractmethod
from typing import Iterable, Optional

from feedback_bot.domain.model import Group


class AbstractGroupRepository(ABC):
    @abstractmethod
    async def get(self, chat_id: int) -> Optional[Group]:
        raise NotImplementedError

    @abstractmethod
    async def get_latest(self) -> Optional[Group]:
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> Group:
        raise NotImplementedError

    @abstractmethod
    async def remove(self, group_chat_id: int) -> Optional[Group]:
        raise NotImplementedError

    @abstractmethod
    async def add(self, group: Group):
        raise NotImplementedError


class InMemoryGroupRepository(AbstractGroupRepository):
    def __init__(self, groups: Optional[Iterable[Group]] = None):
        self.groups = set(groups or ())

    async def get(self, chat_id: int):
        return next(
            filter(
                lambda group: group.chat_id == chat_id,
                self.groups,
            ),
            None,
        )

    async def get_latest(self):
        return max(
            *self.groups,
            key=lambda group: group.created_at,
            default=None,
        )

    async def get_all(self):
        return list(self.groups)
    
    async def remove(self, group_chat_id: int):
        group_to_remove = None
        for group in self.groups:
            if group.chat_id == group_chat_id:
                group_to_remove = group
                break

        if group_to_remove:
            self.groups.remove(group_to_remove)
        return group_to_remove
    
    async def add(self, group: Group):
        self.groups.add(group)