import hashlib
from functools import cache
from typing import List, Optional

from feedback_bot.config import settings
from feedback_bot.model.admin import Admin
from feedback_bot.model.group import Group
from feedback_bot.repositories.admin import AbstractAdminRepository
from feedback_bot.repositories.group import AbstractGroupRepository


def authenticate_admin(
    user_id: int, token: str, admin_repository: AbstractAdminRepository
) -> bool:
    admin = Admin(user_id=user_id)
    admin.authenticate(token)
    admin_repository.add(admin)


def add_group(
    admin_user_id: int,
    group_chat_id: int,
    admin_repository: AbstractAdminRepository,
    group_repository: AbstractGroupRepository,
) -> Optional[Group]:
    admin = admin_repository.get(admin_user_id)
    if not admin:
        return None
    
    if not admin.is_authenticated:
        return None

    group = Group(group_chat_id)
    group_repository.add(group)


def remove_group(group_chat_id: int, group_repository: AbstractGroupRepository):
    group = Group(group_chat_id)
    group_repository.remove(group)


def get_admin_ids(admin_repository: AbstractAdminRepository) -> List[int]:
    admins = admin_repository.get_all()
    return [a.user_id for a in admins]


def get_target_chats(
    admin_repository: AbstractAdminRepository,
    group_repository: AbstractGroupRepository,
) -> List[int]:
    chat_ids: List[int] = []

    admins = admin_repository.get_all()
    chat_ids.extend(a.user_id for a in admins)

    groups = group_repository.get_all()
    chat_ids.extend(g.chat_id for g in groups)

    return chat_ids