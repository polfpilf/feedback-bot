import aiogram
from dependency_injector.providers import (
    Configuration, Dependency, Factory, Provider, Singleton, Resource
)
from dependency_injector import providers, containers

from feedback_bot.config import settings
from feedback_bot.adapters import telegram
from feedback_bot.database import init_connection_pool
from feedback_bot.service_layer import unit_of_work


class Container(containers.DeclarativeContainer):
    config = Configuration(default=settings.as_dict())

    bot = Singleton(aiogram.Bot, config.TELEGRAM_BOT_TOKEN)
    telegram_api: Provider[telegram.AbstractTelegramAPI] = Factory(
        telegram.TelegramAPI,
        bot=bot,
    )

    pool = Resource(init_connection_pool, dsn=config.DATABASE_URL)
    uow: Provider[unit_of_work.AbstractUnitOfWork] = Factory(
        unit_of_work.PostgresUnitOfWork,
        pool=pool
    )
