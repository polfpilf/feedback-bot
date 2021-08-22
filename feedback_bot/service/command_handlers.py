import asyncio
from typing import Union

from feedback_bot.domain import commands, model

from .unit_of_work import AbstractUnitOfWork


class AuthenticationFailedException(Exception):
    """Raised when admin doesn't pass authentication."""

    def __init__(self):
        super().__init__("Authentication has failed")


async def authenticate_admin(
    uow: AbstractUnitOfWork,
    command: commands.AuthenticateAdmin,
):
    async with uow:
        admin = model.Admin.authenticate(
            user_id=command.user_id, token=command.token
        )
        if not admin:
            raise AuthenticationFailedException

        await uow.admin_repository.add(admin)
        await uow.telegram_api.send_message(
            to_chat_id=admin.user_id,
            text=f"Auth token is verified",
        )
        await uow.commit()


async def add_group(
    uow: AbstractUnitOfWork,
    command: commands.AddGroup,
):
    async with uow:
        admin = uow.admin_repository.get(command.by_user_id)
        if not admin:
            return
        
        group = model.TargetChats().add_group(admin=admin, group_chat_id=command.group_id)
        await uow.group_repository.add(group)
        await uow.commit()


async def remove_group(
    uow: AbstractUnitOfWork,
    command: commands.RemoveGroup,
):
    async with uow:
        admin = uow.admin_repository.get(command.by_user_id)
        if not admin:
            return

        group = model.Group(command.group_id)
        await uow.group_repository.remove(group)
        await uow.commit()


async def forward_incoming_message(
    uow: AbstractUnitOfWork,
    command: commands.ForwardIncomingMessage,
):
    async with uow:
        target_chat_ids = model.TargetChats(
            admins=uow.admin_repository.get_all(),
            groups=uow.group_repository.get_all(),
        ).get_target_chat_ids()

        forward_message_coros = [
            uow.telegram_api.forward_message(
                from_chat_id=command.from_chat_id,
                to_chat_id=to_chat_id,
                message_id=message_id,
            )
            for to_chat_id in target_chat_ids
        ]
        forwarded_messages = await asyncio.gather(*forward_incoming_message)
        await uow.message_repository.add_many(forwarded_messages)
        await uow.commit()


async def forward_reply(
    uow: AbstractUnitOfWork,
    command: commands.ForwardReply,
):
    async with uow:
        from_target_chat: Union[model.Admin, model.Group, None] = None
        if command.from_chat_type is model.ChatType.PRIVATE:
            from_target_chat = await uow.admin_repository.get(command.from_chat_id)
        else:
            from_target_chat = await uow.group_repository.get(command.from_chat_id)

        if not from_target_chat:
            # TODO: handle forward detection in less hacky manner
            await forward_incoming_message(
                uow=uow,
                command=commands.ForwardIncomingMessage(
                    from_chat_id=command.from_chat_id,
                    message_id=command.message_id,
                )
            )
            return
        
        forwarded_mesage = await uow.message_repository.get(
            forwarded_message_id=command.reply_to_message_id,
            destination_chat_id=command.from_chat_id,
        )
        if not forwarded_mesage:
            return

        await uow.telegram_api.copy_message(
            from_chat_id=command.from_chat_id,
            to_chat_id=forwarded_message.from_chat_id,
            message_id=command.message_id,
        )
