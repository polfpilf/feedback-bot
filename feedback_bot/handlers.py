import asyncio
import hashlib
from functools import cache
from logging import getLogger

from aiogram import types

from feedback_bot.config import settings
from feedback_bot.model.admin import AuthenticationFailedException
from feedback_bot.repositories.admin import InMemoryAdminRepository
from feedback_bot.repositories.group import InMemoryGroupRepository
from feedback_bot import services

log = getLogger(__name__)

admin_repository = InMemoryAdminRepository()
group_repository = InMemoryGroupRepository()


async def authenticate_admin(message: types.Message):
    log.info('Admin authentication initialized by %d', message.from_user.id)

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
        log.info('Admin authentication failed for %d', message.from_user.id)
        reply_msg = str(e)
    else:
        log.info('Admin authentication passed for %d', message.from_user.id)
        reply_msg = "Auth token is verified"

    await message.reply(reply_msg)


async def update_group(my_chat_member: types.ChatMemberUpdated):
    admin_ids = services.get_admin_ids(admin_repository=admin_repository)

    admin_message: str
    if my_chat_member.new_chat_member.status in ("kicked", "left"):
        log.info(
            'Bot kicked from chat %d "%s" by user %d',
            my_chat_member.chat.id,
            my_chat_member.chat.title,
            my_chat_member.from_user.id,
        )
        services.remove_group(
            group_chat_id=my_chat_member.chat.id,
            group_repository=group_repository
        )
        admin_message = f"Group {my_chat_member.chat.title} has been removed"
    else:
        if my_chat_member.from_user.id not in admin_ids:
            log.info(
                'Bot added to chat %d "%s" by non-admin user %d. Ignoring.',
                my_chat_member.chat.id,
                my_chat_member.chat.title,
                my_chat_member.from_user.id,
            )
            return

        log.info(
            'Bot added to chat %d "%s" by admin %d',
            my_chat_member.chat.id,
            my_chat_member.chat.title,
            my_chat_member.from_user.id,
        )
        services.add_group(
            admin_user_id=my_chat_member.from_user.id,
            group_chat_id=my_chat_member.chat.id,
            admin_repository=admin_repository,
            group_repository=group_repository,
        )
        admin_message = f"Group {my_chat_member.chat.title} has been added"

    admin_message_coros = [
        my_chat_member.bot.send_message(chat_id, admin_message)
        for chat_id in admin_chat_ids
    ]
    await asyncio.gather(*admin_message_coros)


async def forward_incoming_message(message: types.Message):
    if message.is_command():
        log.info("Ignoring incoming message as it's a command")
        return

    target_chat_ids = services.get_target_chats(
        admin_repository=admin_repository,
        group_repository=group_repository
    )
    log.info(
        'Forwarding incoming message %d to chats: %s',
        message.message_id,
        target_chat_ids,
    )
    forward_message_coros = [message.forward(chat_id) for chat_id in target_chat_ids]
    await asyncio.gather(*forward_message_coros)


async def forward_reply(message: types.Message):
    target_chat_ids = services.get_target_chats(
        admin_repository=admin_repository,
        group_repository=group_repository,
    )
    if not message.chat.id in target_chat_ids:
        log.info(
            "Ignoring message from chat %d as it's not a target chat",
            message.chat.id,
        )
        return

    log.info(
        "Copying message from chat %d to reply client %d",
        message.chat.id,
        message.reply_to_message.chat.id,
    )
    print(message.reply_to_message)
    await message.copy_to(message.reply_to_message.forward_from_chat.id)
