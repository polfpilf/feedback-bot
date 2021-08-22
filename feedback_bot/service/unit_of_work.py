from abc import ABCMeta, abstractmethod
from contextlib import AbstractAsyncContextManager

from feedback_bot.adapters.repositories.admin import AbstractAdminRepository
from feedback_bot.adapters.repositories.group import AbstractGroupRepository
from feedback_bot.adapters.repositories.forwarded_message import AbstractMessageRepository
from feedback_bot.adapters.telegram import AbstractTelegramAPI


class AbstractUnitOfWork(AbstractAsyncContextManager, meta=ABCMeta):
    admin_repository: AbstractAdminRepository
    group_repository: AbstractGroupRepository
    message_repository: AbstractMessageRepository
    telegram_api: AbstractTelegramAPI

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args, **kwargs):
        await self.rollback()

    @abstractmethod
    async def rollback(self):
        raise NotImplementedError

    @abstractmethod
    async def commit(self):
        raise NotImplementedError


