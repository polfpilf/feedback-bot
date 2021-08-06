from aiogram import Bot, Dispatcher, executor

from feedback_bot.config import settings


def create_dispatcher():
    bot = Bot(settings.TELEGRAM_BOT_TOKEN)
    return Dispatcher(bot)


async def set_webhook(dp: Dispatcher):
    webhook_url = f"{settings.TELEGRAM_WEBHOOK_HOST}{settings.TELEGRAM_WEBHOOK_PATH}"
    await dp.bot.set_webhook(webhook_url)


def start_bot():
    dp = create_dispatcher()
    executor.start_webhook(
        dp,
        on_startup=set_webhook,
        webhook_path=settings.TELEGRAM_WEBHOOK_PATH,
        host=settings.HOST,
        port=settings.PORT,
    )