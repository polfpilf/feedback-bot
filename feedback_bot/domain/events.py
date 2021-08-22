from dataclasses import dataclass


class BaseEvent:
    pass


@dataclass
class AdminAdded:
    admin_user_id: int


@dataclass
class TargetChatAdded:
    chat_id: int


@dataclass
class TargetChatRemoved:
    chat_id: int
