import aiogram
import asyncpg
from dependency_injector.providers import (
    Configuration,
    Factory,
    Provider,
    Resource,
    Singleton,
)
from dependency_injector.containers import DeclarativeContainer

from feedback_bot.adapters import telegram
from feedback_bot.config import settings
from feedback_bot.service_layer import unit_of_work


async def init_connection_pool(dsn: str):
    async with asyncpg.create_pool(dsn=dsn) as pool:
        yield pool


class Container(DeclarativeContainer):
    config = Configuration(default=settings.as_dict())

    bot = Singleton(aiogram.Bot, config.TELEGRAM_BOT_TOKEN)
    telegram_api: Provider[telegram.AbstractTelegramAPI] = Factory(
        telegram.TelegramAPI,
        bot=bot,
    )

    pool = Resource(init_connection_pool, dsn=config.DATABASE_URL)
    uow: Provider[unit_of_work.AbstractUnitOfWork] = Factory(
        unit_of_work.PostgresUnitOfWork,
        bot=bot,
        pool=pool
    )
