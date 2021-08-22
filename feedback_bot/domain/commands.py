from dataclasses import dataclass
from enum import Enum


class BaseCommand:
    pass


@dataclass
class AuthenticateAdmin(BaseCommand):
    user_id: int
    token: str


@dataclass
class AddGroup(BaseCommand):
    by_user_id: int
    group_id: int


@dataclass
class RemoveGroup(BaseCommand):
    group_id: int


@dataclass
class ForwardIncomingMessage(BaseCommand):
    from_chat_id: int
    message_id: int


class ChatType(str, Enum):
    PRIVATE = "private"
    GROUP = "group"


@dataclass
class ForwardReply(BaseCommand):
    from_chat_id: int
    from_chat_type: ChatType
    message_id: int
    reply_to_message_id: int
