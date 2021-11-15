from abc import ABC, abstractmethod
from typing import Dict, Iterable, Optional, Tuple

import asyncpg

from feedback_bot.model import ForwardedMessage


class AbstractForwardedMessageRepository(ABC):
    @abstractmethod
    async def get(
        self, forwarded_message_id: int, target_chat_id: int
    ) -> Optional[ForwardedMessage]:
        raise NotImplementedError

    @abstractmethod
    async def add(self, forwarded_message: ForwardedMessage):
        raise NotImplementedError


class PostgresForwardedMessageRepository(AbstractForwardedMessageRepository):
    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn

    async def get(
        self, forwarded_message_id: int, target_chat_id: int
    ):
        row = await self._conn.fetchrow(
            """
            SELECT
                forwarded_message_id,
                target_chat_id,
                origin_chat_id,
                created_at
            FROM
                forwarded_message
            WHERE
                forwarded_message_id = $1
                AND target_chat_id = $2
            """,
            forwarded_message_id,
            target_chat_id,
        )
        if not row:
            return None

        return ForwardedMessage(**row)

    async def add(self, forwarded_message: ForwardedMessage):
        await self._conn.execute(
            """
            INSERT INTO forwarded_message (
                forwarded_message_id,
                target_chat_id,
                origin_chat_id,
                created_at
            )
            VALUES ($1, $2, $3, $4)
            """,
            forwarded_message.forwarded_message_id,
            forwarded_message.target_chat_id,
            forwarded_message.origin_chat_id,
            forwarded_message.created_at,
        )
