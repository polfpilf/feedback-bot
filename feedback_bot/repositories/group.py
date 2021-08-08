from abc import ABC, abstractmethod

from feedback_bot.model.group import Group

class AbstractGroupRepository(ABC):
    @abstractmethod
    def get_all(self) -> Group:
        raise NotImplementedError

    @abstractmethod
    def remove(self, group: Group):
        raise NotImplementedError

    @abstractmethod
    def add(self, group: Group):
        raise NotImplementedError


class InMemoryGroupRepository(AbstractGroupRepository):
    def __init__(self):
        self.groups = set()

    def get_all(self):
        return list(self.groups)
    
    def remove(self, group: Group):
        self.groups.discard(group)
    
    def add(self, group: Group):
        self.groups.add(group)