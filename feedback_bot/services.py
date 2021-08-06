import hashlib
from functools import cache

from feedback_bot.config import settings
from feedback_bot.model.admin import Admin
from feedback_bot.repositories.admin import AbstractAdminRepository


def get_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@cache
def get_admin_token_hash() -> str:
    return get_token_hash(settings.ADMIN_TOKEN)


def authenticate_admin(
    user_id: int, token: str, admin_repository: AbstractAdminRepository
) -> bool:
    admin = Admin(user_id=user_id)
    admin.authenticate(token)
    admin_repository.add(admin)