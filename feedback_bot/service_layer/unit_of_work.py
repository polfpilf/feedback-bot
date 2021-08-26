from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import Dict, Tuple

import asyncpg
from aiogram import Bot

from feedback_bot.adapters.repositories import (
    admin as admin_repository,
    target_chat as target_chat_repository,
    forwarded_message as forwarded_message_repository,
)
from feedback_bot.adapters import telegram
from feedback_bot.model import Admin, TargetChat, ForwardedMessage


class AbstractUnitOfWork(AbstractAsyncContextManager):
    admin_repository: admin_repository.AbstractAdminRepository
    target_chat_repository: target_chat_repository.AbstractTargetChatRepository
    forwarded_message_repository: forwarded_message_repository.AbstractForwardedMessageRepository
    telegram_api: telegram.AbstractTelegramAPI

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





class PostgresUnitOfWork(AbstractUnitOfWork):
    _pool: asyncpg.Pool
    _conn: asyncpg.Connection
    _transaction: asyncpg.transaction.Transaction

    def __init__(self, pool: asyncpg.Pool):
        self._pool = pool

    async def __aenter__(self):
        self._conn = await self._pool.acquire()
        self._transaction = await self._conn.transaction()
        await self._transaction.start()

        self.admin_repository = None

    async def __aexit__(self, *args, **kwargs):
        super().__aexit__(*args, **kwargs)
        await self._pool.release(self._conn)

    async def commit(self):
        await self._transaction.commit()

    async def rollback(self):
        await self._transaction.rollback()
