from abc import abstractmethod, ABC
from typing import Iterable, Optional, List, Dict

import asyncpg

from feedback_bot.model import Admin, TargetChat


class AbstractAdminRepository(ABC):
    @abstractmethod
    async def get(self, user_id: int) -> Optional[Admin]:
        raise NotImplementedError

    @abstractmethod
    async def get_all(self) -> List[Admin]:
        raise NotImplementedError

    @abstractmethod
    async def add(self, admin: Admin):
        raise NotImplementedError


class PostgresAdminRepository(AbstractAdminRepository):
    def __init__(self, conn: asyncpg.Connection):
        self._conn = conn

    @staticmethod
    def row_to_model(row: asyncpg.Record) -> Admin:
        target_chat = TargetChat(
            chat_id=row["target_chat_id"],
            created_at=row["target_chat_created_at"],
        )
        return Admin(user_id=row["user_id"], target_chat=target_chat)

    async def get(self, user_id: int):
        row = await self._conn.fetchrow(
            """
            SELECT
                admin.user_id AS user_id,
                target_chat.chat_id AS target_chat_id,
                target_chat.created_at AS target_chat_created_at
            FROM
                admin INNER JOIN target_chat
                    ON admin.target_chat_id = target_chat.chat_id
            WHERE
                admin.user_id = $1
            """,
            user_id,
        )
        if not row:
            return None
        
        return self.row_to_model(row)

    async def get_all(self):
        rows = await self._conn.fetch(
            """
            SELECT
                admin.user_id AS user_id,
                target_chat.chat_id AS target_chat_id,
                target_chat.created_at AS target_chat_created_at
            FROM
                admin INNER JOIN target_chat
                    ON admin.target_chat_id = target_chat.chat_id
            """
        )
        return [self.row_to_model(row) for row in rows]

    async def add(self, admin: Admin):
        await self._conn.execute(
            """
            INSERT INTO target_chat (chat_id, created_at)
            VALUES ($1, $2)
            """,
            admin.target_chat.chat_id, admin.target_chat.created_at
        )
        await self._conn.execute(
            """
            INSERT INTO admin (user_id, target_chat_id)
            VALUES ($1, $2)
            """,
            admin.user_id, admin.target_chat.chat_id
        )
