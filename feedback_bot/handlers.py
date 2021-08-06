import hashlib
from functools import cache

from aiogram import types

from feedback_bot.config import settings


def get_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


@cache
def get_auth_token_hash():
    return get_token_hash(settings.ADMIN_TOKEN)


async def authenticate_admin(message: types.Message):
    auth_token = message.get_args()
    if not auth_token:
        await message.reply("Auth token is required")
        return

    if get_token_hash(auth_token) != get_auth_token_hash():
        await message.reply("Auth token is invalid")
        return
    
    await message.reply("Auth token is verified!")