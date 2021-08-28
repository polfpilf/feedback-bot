from abc import ABC, abstractmethod
from typing import Dict, Iterable, Optional

import asyncpg

from feedback_bot.model import TargetChat


class AbstractTargetChatRepository(ABC):
    @abstractmethod
    async def get(self, chat_id: int) -> Optional[TargetChat]:
        raise NotImplemented

    @abstractmethod
    async def get_latest(self) -> Optional[TargetChat]:
        raise NotImplementedError

    @abstractmethod
    async def remove(self, chat_id: int) -> Optional[TargetChat]:
        raise NotImplementedError

    @abstractmethod
    async def add(self, target_chat: TargetChat):
        raise NotImplementedError


class PostgresTargetChatRepository(AbstractTargetChatRepository):
    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn

    @staticmethod
    def row_to_model(row: asyncpg.Record) -> TargetChat:
        return TargetChat(**row)

    async def get(self, chat_id: int):
        row = await self._conn.fetchrow(
            """
            SELECT
                chat_id,
                created_at
            FROM
                target_chat
            WHERE
                chat_id = $1
            """,
            chat_id
        )
        if not row:
            return None
        
        return self.row_to_model(row)

    async def get_latest(self):
        row = await self._conn.fetchrow(
            """
            SELECT
                chat_id,
                created_at
            FROM
                target_chat
            ORDER BY created_at DESC
            LIMIT 1
            """
        )
        if not row:
            return None
        
        return self.row_to_model(row)

    async def remove(self, chat_id: int):
        row = await self._conn.fetchrow(
            """
            DELETE
            FROM
                target_chat
            WHERE
                chat_id = $1
            RETURNING chat_id, created_at
            """,
            chat_id
        )
        if not row:
            return None
        
        return self.row_to_model(row)

    async def add(self, target_chat: TargetChat):
        await self._conn.execute(
            """
            INSERT INTO target_chat (chat_id, created_at)
            VALUES ($1, $2)
            """,
            target_chat.chat_id, target_chat.created_at
        )
