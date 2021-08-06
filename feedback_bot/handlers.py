import hashlib
from functools import cache

from aiogram import types

from feedback_bot.config import settings
from feedback_bot.model.admin import AuthenticationFailedException
from feedback_bot.repositories.admin import InMemoryAdminRepository
from feedback_bot import services


admin_repository = InMemoryAdminRepository()


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