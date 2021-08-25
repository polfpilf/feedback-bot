import logging

from aiogram import Bot, Dispatcher, executor, types
from dependency_injector.wiring import inject, Provide

from feedback_bot.bootstrap import Container
from feedback_bot.service_layer import services

log = logging.getLogger(__name__)


async def authenticate_admin(message: types.Message):
    log.debug('Admin authentication command issued by user_id=%d', message.from_user.id)

    token = message.get_args()
    if not token:
        return

    await services.authenticate_admin(
        user_id=message.from_user.id,
        chat_id=message.chat.id,
        token=token,
    )


async def update_group(my_chat_member: types.ChatMemberUpdated):
    if my_chat_member.new_chat_member.status in ("kicked", "left"):
        log.debug(
            'Bot kicked from group %d "%s" by user_id=%d',
            my_chat_member.chat.id,
            my_chat_member.chat.title,
            my_chat_member.from_user.id,
        )
        await services.remove_group(group_chat_id=my_chat_member.chat.id)
    else:
        log.debug(
            'Bot added to group %d "%s" by user_id=%d',
            my_chat_member.chat.id,
            my_chat_member.chat.title,
            my_chat_member.from_user.id,
        )
        await services.add_group(
            by_user_id=my_chat_member.from_user.id,
            group_chat_id=my_chat_member.chat.id,
        )


async def forward_incoming_message(message: types.Message):
    log.debug(
        "Processing incoming message message_id=%d chat_id=%d",
        message.message_id,
        message.chat.id,
    )

    if message.is_command():
        log.debug("Ignoring incoming message as it's a command")
        return

    await services.forward_incoming_message(
        origin_chat_id=message.chat.id,
        message_id=message.message_id,
    )


async def forward_reply(message: types.Message):
    log.debug(
        "Processing reply. message_id=%d, chat_id=%d",
        message.message_id,
        message.chat.id
    )
    await services.forward_reply(
        target_chat_id=message.chat.id,
        forwarded_message_id=message.reply_to_message.message_id,
        reply_message_id=message.message_id,
    )


def create_dispatcher(bot: Bot):
    dp = Dispatcher(bot)

    dp.register_my_chat_member_handler(update_group)
    dp.register_message_handler(
        authenticate_admin, chat_type='private', commands=["auth"]
    )
    dp.register_message_handler(forward_reply, is_reply=True)
    dp.register_message_handler(forward_incoming_message, chat_type='private', is_reply=False)
    
    return dp


@inject
async def set_webhook(
    dp: Dispatcher,
    webhook_host: str = Provide[Container.config.TELEGRAM_WEBHOOK_HOST],
    webhook_path: str = Provide[Container.config.TELEGRAM_WEBHOOK_PATH]
):
    webhook_url = f"{webhook_host}{webhook_path}"
    await dp.bot.set_webhook(webhook_url)


@inject
def start_bot(
    bot: Bot = Provide[Container.bot],
    webhook_path: str = Provide[Container.config.TELEGRAM_WEBHOOK_PATH],
    host: str = Provide[Container.config.HOST],
    port: int = Provide[Container.config.PORT],
):
    dp = create_dispatcher(bot)
    executor.start_webhook(
        dp,
        on_startup=set_webhook,
        webhook_path=webhook_path,
        host=host,
        port=port,
        access_log=logging.getLogger('access_log'),
    )