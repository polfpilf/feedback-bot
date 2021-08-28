from abc import ABC, abstractmethod
from contextlib import AbstractAsyncContextManager
from dataclasses import dataclass
from typing import Dict, Tuple

import aiogram
import asyncpg

from feedback_bot.adapters import telegram
from feedback_bot.adapters.repositories import (
    admin as admin_repository,
    target_chat as target_chat_repository,
    forwarded_message as forwarded_message_repository,
)
from feedback_bot.model import Admin, TargetChat, ForwardedMessage


class AbstractUnitOfWork(AbstractAsyncContextManager):
    admins: admin_repository.AbstractAdminRepository
    target_chats: target_chat_repository.AbstractTargetChatRepository
    forwarded_messages: forwarded_message_repository.AbstractForwardedMessageRepository
    telegram_api: telegram.AbstractTelegramAPI

    _rolled_back: bool
    _committed: bool

    def __init__(self):
        self._rolled_back = False
        self._committed = False

    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        if self._rolled_back or self._committed:
            return

        await self.rollback()

    @abstractmethod
    async def _rollback(self):
        raise NotImplementedError

    async def rollback(self):
        self._rolled_back = True
        await self._rollback()

    @abstractmethod
    async def _commit(self):
        raise NotImplementedError

    async def commit(self):
        self._committed = True
        await self._commit()


class PostgresUnitOfWork(AbstractUnitOfWork):
    _pool: asyncpg.Pool
    _conn: asyncpg.Connection
    _transaction: asyncpg.transaction.Transaction

    _committed: bool
    _rolled_back: bool

    def __init__(self, bot: aiogram.Bot, pool: asyncpg.Pool):
        super().__init__()

        self.telegram_api = telegram.TelegramAPI(bot)
        self._pool = pool

    async def __aenter__(self):
        self._conn = await self._pool.acquire()
        self._transaction = self._conn.transaction()
        await self._transaction.start()

        self.admins = admin_repository.PostgresAdminRepository(self._conn)
        self.target_chats = (
            target_chat_repository.PostgresTargetChatRepository(self._conn)
        )
        self.forwarded_messages = (
            forwarded_message_repository.PostgresForwardedMessageRepository(self._conn)
        )

    async def __aexit__(self, *args):
        await super().__aexit__(*args)
        await self._pool.release(self._conn)

    async def _commit(self):
        await self._transaction.commit()

    async def _rollback(self):
        await self._transaction.rollback()
