from dependency_injector import providers

from feedback_bot import bootstrap
from feedback_bot import bot
from feedback_bot.service_layer import services
from feedback_bot.service_layer.unit_of_work import InMemoryUnitOfWork


if __name__ == "__main__":
    container = bootstrap.Container()

    # TODO: remove after DB integration
    admins = {}
    target_chats = {}
    forwarded_messages = {}

    container.uow.override(
        providers.Factory(
            InMemoryUnitOfWork,
            bot=container.bot,
            admins=admins,
            target_chats=target_chats,
            forwarded_messages=forwarded_messages,
        )
    )

    container.wire(modules=[bot, services])

    bot.start_bot()