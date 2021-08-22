from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Type, TypeVar

from feedback_bot.config import settings

from .events import AdminAdded, BaseEvent, TargetChatAdded, TargetChatRemoved


class BaseAggregate(Protocol):
    events: List[BaseEvent]

    def __init__(self):
        self.events = []


T = TypeVar("T")


class TargetChat(BaseAggregate):
    def __init__(sel, chat_id: int, created_at: Optional[datetime] = None):
        super().__init__()
        self.chat_id = chat_id
        self.created_at = created_at or datetime.utcnow()

    @classmethod
    def create(cls: Type[T], chat_id: int) -> T:
        chat = cls(chat_id=chat_id)
        chat.events.append(TargetChatAdded(chat_id=chat_id))
        return chat

    def remove(self):
        self.events.append(TargetChatRemoved(chat_id=self.chat_id))


class Admin(BaseAggregate):
    def __init__(self, user_id: int, created_at: Optional[datetime] = None):
        super().__init__()
        self.user_id = user_id
        self.created_at = created_at or datetime.utcnow()

    @classmethod
    def authenticate(cls: Type[T], user_id: int, token: str) -> Optional[T]:
        if token != settings.ADMIN_TOKEN:
            return None
        admin = cls(user_id=user_id)
        return admin


@dataclass(eq=True, frozen=True)
class ForwardedMessage:
    from_chat_id: int
    forwarded_message_id: int
    destination_chat_id: int


@dataclass
class TargetChats:
    events: List = field(default_factory=list)

    def get_target_chat_id(
        self,
        latest_admin: Optional[Admin],
        latest_group: Optional[Group],
    ) -> Optional[int]:
        non_empty_targets = []
        if latest_admin:
            non_empty_targets.append((latest_admin.created_at, latest_admin.user_id))
        if latest_group:
            non_empty_targets.append((latest_group.created_at, latest_group.chat_id))
        
        latest_target = max(non_empty_targets, default=None)
        return latest_target and latest_target[1]

    def authenticate_admin(self, admin_user_id: int, token: str) > Optional[Admin]:
        if token != settings.ADMIN_TOKEN:
            return None

        admin = Admin(user_id=admin_user_id) 
        self.events.append(AdminAdded(admin_user_id=admin.user_id))
        return admin
    
    def add_group(self, admin: Admin, group_chat_id: int) -> Group:
        group = Group(chat_id=group_chat_id)
        self.events.append(
            GroupAdded(
                group_chat_id=group.chat_id,
                by_admin_user_id=admin.user_id,
            )
        )
        return group

    def remove_group(self, admin: Admin, group: Group):
        self.events.append(
            GroupAdded(
                group_chat_id=group.chat_id,
                by_admin_user_id=admin.user_id,
            )
        )
