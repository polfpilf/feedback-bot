from feedback_bot import bot, bootstrap
from feedback_bot.service_layer import services


def inject_dependencies():
    container = bootstrap.Container()

    # TODO: remove after DB integration
    from dependency_injector import providers

    from feedback_bot.service_layer.unit_of_work import InMemoryUnitOfWork

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
    return container


def main():
    inject_dependencies()
    bot.start_bot()