import asyncio
import hashlib
from functools import cache

from aiogram import types

from feedback_bot.config import settings
from feedback_bot.model.admin import AuthenticationFailedException
from feedback_bot.repositories.admin import InMemoryAdminRepository
from feedback_bot.repositories.group import InMemoryGroupRepository
from feedback_bot import services


admin_repository = InMemoryAdminRepository()
group_repository = InMemoryGroupRepository()


async def authenticate_admin(message: types.Message):
    token = message.get_args()
    if not token:
        await message.reply("Auth token is required")
        return

    reply_msg: str
    try:
        services.authenticate_admin(
            user_id=message.from_user.id,
            token=token,
            admin_repository=admin_repository,
        )
    except AuthenticationFailedException as e:
        reply_msg = str(e)
    else:
        reply_msg = "Auth token is verified"

    await message.reply(reply_msg)


async def update_group(my_chat_member: types.ChatMemberUpdated):
    admin_message: str
    if my_chat_member.new_chat_member.status in ("kicked", "left"):
        services.remove_group(
            group_chat_id=my_chat_member.chat.id,
            group_repository=group_repository
        )
        admin_message = f"Group {my_chat_member.chat.title} has been removed"
    else:
        services.add_group(
            admin_user_id=my_chat_member.from_user.id,
            group_chat_id=my_chat_member.chat.id,
            admin_repository=admin_repository,
            group_repository=group_repository,
        )
        admin_message = f"Group {my_chat_member.chat.title} has been added"

    admin_chat_ids = services.get_admin_chats(admin_repository=admin_repository)
    admin_message_coros = [
        my_chat_member.bot.send_message(chat_id, admin_message)
        for chat_id in admin_chat_ids
    ]
    await asyncio.gather(*admin_message_coros)