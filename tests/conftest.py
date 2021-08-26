from pytest import fixture

from feedback_bot.main import inject_dependencies


@fixture
def container():
    dep_container = inject_dependencies()
    yield dep_container
    dep_container.unwire()
