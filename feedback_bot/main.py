from feedback_bot import bot, bootstrap
from feedback_bot.service_layer import services


def inject_dependencies() -> bootstrap.Container:
    container = bootstrap.Container()
    container.wire(modules=[bot, services])
    return container


def main():
    inject_dependencies()
    bot.start_bot()