from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Type, TypeVar

T = TypeVar('T')


def _utc_now():
    """Return current UTC timezone-aware datetime"""
    return datetime.now(timezone.utc)


@dataclass(frozen=True, eq=True)
class TargetChat:
    chat_id: int
    created_at: datetime = field(default_factory=_utc_now)


@dataclass(frozen=True, eq=True)
class Admin:
    user_id: int
    target_chat: TargetChat

    @classmethod
    def authenticate(
        cls: Type[T],
        user_id: int,
        chat_id: int,
        token: str,
        admin_token: str,
    ) -> Optional[T]:
        if token != admin_token:
            return None

        target_chat = TargetChat(chat_id=chat_id)
        return cls(user_id=user_id, target_chat=target_chat)


@dataclass(frozen=True, eq=True)
class ForwardedMessage:
    forwarded_message_id: int
    target_chat_id: int
    origin_chat_id: int = field(hash=False, compare=False)
    created_at: datetime = field(hash=False, compare=False, default_factory=_utc_now)
