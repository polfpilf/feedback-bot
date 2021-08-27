import asyncio

import pytest

from feedback_bot.main import inject_dependencies


@pytest.fixture(scope='session')
def event_loop():
    """Override function-scoped event-loop fixture from pytest-asyncio."""
    loop = asyncio.get_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def container():
    dep_container = inject_dependencies()
    yield dep_container
    dep_container.unwire()
