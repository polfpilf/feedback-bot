import logging

from aiogram import Bot, Dispatcher, executor, types

from feedback_bot import handlers
from feedback_bot.config import settings


def create_dispatcher():
    bot = Bot(settings.TELEGRAM_BOT_TOKEN)
    dp = Dispatcher(bot)

    dp.register_my_chat_member_handler(handlers.update_group)
    dp.register_message_handler(
        handlers.authenticate_admin, chat_type='private', commands=["auth"]
    )
    dp.register_message_handler(handlers.forward_reply, chat_type='private', is_reply=True)
    dp.register_message_handler(handlers.forward_incoming_message, chat_type='private', is_reply=False)
    
    return dp


async def set_webhook(dp: Dispatcher):
    webhook_url = f"{settings.TELEGRAM_WEBHOOK_HOST}{settings.TELEGRAM_WEBHOOK_PATH}"
    await dp.bot.set_webhook(webhook_url)


def start_bot():
    logging.basicConfig(level=logging.DEBUG)

    dp = create_dispatcher()
    executor.start_webhook(
        dp,
        on_startup=set_webhook,
        webhook_path=settings.TELEGRAM_WEBHOOK_PATH,
        host=settings.HOST,
        port=settings.PORT,
        access_log=logging.getLogger('access_log'),
    )