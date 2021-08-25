from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Type, TypeVar

from feedback_bot.config import settings


T = TypeVar('T')


@dataclass(frozen=True, eq=True)
class TargetChat:
    chat_id: int
    created_at: datetime = field(
        default_factory=datetime.utcnow,
        hash=False,
        compare=False,
    )


@dataclass(frozen=True, eq=True)
class Admin:
    user_id: int
    target_chat: TargetChat
    created_at: datetime = field(
        default_factory=datetime.utcnow,
        hash=False,
        compare=False,
    )

    @classmethod
    def authenticate(cls: Type[T], user_id: int, chat_id: int, token: str) -> Optional[T]:
        if token != settings.ADMIN_TOKEN:
            return None

        target_chat = TargetChat(chat_id=chat_id)
        return cls(user_id=user_id, target_chat=target_chat)


@dataclass(frozen=True, eq=True)
class ForwardedMessage:
    forwarded_message_id: int
    target_chat_id: int
    origin_chat_id: int
