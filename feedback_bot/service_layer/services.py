import asyncio
from logging import getLogger
from typing import List, Optional

from dependency_injector.wiring import inject, Provide

from feedback_bot.bootstrap import Container
from feedback_bot.config import settings
from feedback_bot.model import Admin, ForwardedMessage, TargetChat

from .unit_of_work import AbstractUnitOfWork


log = getLogger(__name__)


@inject
async def authenticate_admin(
    user_id: int,
    chat_id: int,
    token: str,
    uow: AbstractUnitOfWork = Provide[Container.uow],
    admin_token: str = Provide[Container.config.ADMIN_TOKEN],
):
    async with uow:
        existing_admin = await uow.admins.get(user_id)
        if existing_admin:
            return

        admin = Admin.authenticate(
            user_id=user_id,
            chat_id=chat_id,
            token=token,
            admin_token=admin_token,
        )
        if not admin:
            log.debug("User user_id: %d is not an admin", user_id)
            return

        await uow.admins.add(admin)
        await uow.telegram_api.send_message(
            to_chat_id=admin.target_chat.chat_id,
            text="Auth token successfully verified",
        )
        await uow.commit()


@inject
async def add_group(
    by_user_id: int,
    group_chat_id: int,
    uow: AbstractUnitOfWork = Provide[Container.uow],
):
    async with uow:
        admin = await uow.admins.get(user_id=by_user_id)
        if not admin:
            log.debug("User user_id: %d is not an admin", by_user_id)
            return

        group_chat = TargetChat(chat_id=group_chat_id)
        await uow.target_chats.add(group_chat)

        admins = await uow.admins.get_all()
        notify_admin_coros = [
            uow.telegram_api.send_message(
                to_chat_id=admin.target_chat.chat_id,
                text=f"Group chat {group_chat_id} added"
            )
            for admin in admins
        ]
        await asyncio.gather(*notify_admin_coros)
        await uow.commit()


@inject
async def remove_group(
    group_chat_id: int,
    uow: AbstractUnitOfWork = Provide[Container.uow]
):
    async with uow:
        removed_group = await uow.target_chats.remove(chat_id=group_chat_id)
        if not removed_group:
            return

        admins = await uow.admins.get_all()
        notify_admin_coros = [
            uow.telegram_api.send_message(
                to_chat_id=admin.target_chat.chat_id,
                text=f"Group chat {group_chat_id} removed"
            )
            for admin in admins
        ]
        await asyncio.gather(*notify_admin_coros)
        await uow.commit()


@inject
async def forward_incoming_message(
    origin_chat_id: int,
    message_id: int,
    uow: AbstractUnitOfWork = Provide[Container.uow],
):
    async with uow:
        target_chat = await uow.target_chats.get_latest()
        if not target_chat:
            return
        
        forwarded_message_id = await uow.telegram_api.forward_message(
            from_chat_id=origin_chat_id,
            to_chat_id=target_chat.chat_id,
            message_id=message_id,
        )
        forwarded_message = ForwardedMessage(
            forwarded_message_id=forwarded_message_id,
            target_chat_id=target_chat.chat_id,
            origin_chat_id=origin_chat_id,
        )
        await uow.forwarded_messages.add(forwarded_message)
        await uow.commit()


@inject
async def forward_reply(
    target_chat_id: int,
    forwarded_message_id: int,
    reply_message_id: int,
    uow: AbstractUnitOfWork = Provide[Container.uow],
):
    async with uow:
        forwarded_message = await uow.forwarded_messages.get(
            forwarded_message_id=forwarded_message_id,
            target_chat_id=target_chat_id,
        )
        if not forwarded_message:
            return

        await uow.telegram_api.copy_message(
            from_chat_id=target_chat_id,
            to_chat_id=forwarded_message.origin_chat_id,
            message_id=reply_message_id,
        )
