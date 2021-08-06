import hashlib
from datetime import datetime
from dataclasses import dataclass
from functools import cache
from typing import Optional

from feedback_bot.config import settings


def get_token_hash(token: str) -> str:
    # TODO: use stronger hashing algorithm
    return hashlib.sha256(token.encode()).hexdigest()


@cache
def _get_admin_token_hash() -> str:
    return get_token_hash(settings.ADMIN_TOKEN)


def check_token_hash(token_hash: str) -> bool:
    # TODO: use stronger hashing algorithm
    return _get_admin_token_hash() == token_hash


class AuthenticationFailedException(Exception):
    """Raised when admin doesn't pass authentication."""

    def __init__(self):
        super().__init__("Authentication has failed")


@dataclass
class Admin:
    user_id: int
    token_hash: Optional[str] = None

    def __hash__(self):
        return hash(self.user_id)

    def __eq__(self, other):
        return self.user_id == other.user_id
    
    def authenticate(self, token: str):
        if token != settings.ADMIN_TOKEN:
            raise AuthenticationFailedException

        self.token_hash = get_token_hash

    @property
    def is_authenticated(self) -> bool:
        return check_token_hash(self.token_hash)
