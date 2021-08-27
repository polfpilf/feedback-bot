from datetime import datetime, timezone

import asyncpg
import pytest

from feedback_bot.adapters.repositories.admin import PostgresAdminRepository
from feedback_bot.model import Admin, TargetChat


class TestPostgresAdminRepository:
    @pytest.mark.asyncio
    async def test_admin_repository_get(self, db_connection: asyncpg.Connection):
        await db_connection.executemany(
            """
            INSERT INTO target_chat (chat_id, created_at)
            VALUES ($1, $2)
            """,
            [
                (13, datetime(2021, 1, 1, tzinfo=timezone.utc)),
                (37, datetime(2020, 2, 2, tzinfo=timezone.utc)),
            ]
        )
        await db_connection.executemany(
            """
            INSERT INTO admin (user_id, target_chat_id)
            VALUES ($1, $2)
            """,
            [(42, 13), (43, 37)]
        )

        admin_repository = PostgresAdminRepository(db_connection)
        admin = await admin_repository.get(user_id=42)

        assert admin.user_id == 42
        
        assert admin.target_chat.chat_id == 13
        assert admin.target_chat.created_at == datetime(2021, 1, 1, tzinfo=timezone.utc)

    @pytest.mark.asyncio
    async def test_admin_reposiory_get_not_found(self, db_connection: asyncpg.Connection):
        admin_repository = PostgresAdminRepository(db_connection)
        admin = await admin_repository.get(user_id=42)

        assert admin is None

    @pytest.mark.asyncio
    async def test_admin_repository_get_all(self, db_connection: asyncpg.Connection):
        target_chat_1 = TargetChat(
            chat_id=13,
            created_at=datetime(2021, 1, 1, tzinfo=timezone.utc)
        )
        target_chat_2 = TargetChat(
            chat_id=37,
            created_at=datetime(2020, 2, 2, tzinfo=timezone.utc)
        )
        await db_connection.executemany(
            """
            INSERT INTO target_chat (chat_id, created_at)
            VALUES ($1, $2)
            """,
            [
                (13, datetime(2021, 1, 1, tzinfo=timezone.utc)),
                (37, datetime(2020, 2, 2, tzinfo=timezone.utc)),
            ]
        )

        admin_1 = Admin(user_id=42, target_chat=target_chat_1)
        admin_2 = Admin(user_id=43, target_chat=target_chat_2)
        await db_connection.executemany(
            """
            INSERT INTO admin (user_id, target_chat_id)
            VALUES ($1, $2)
            """,
            [(42, 13), (43, 37)]
        )

        admin_repository = PostgresAdminRepository(db_connection)
        admins = await admin_repository.get_all()

        assert set(admins) == set((admin_1, admin_2))

    @pytest.mark.asyncio
    async def test_admin_repository_add(self, db_connection: asyncpg.Connection):
        target_chat = TargetChat(
            chat_id=13, created_at=datetime(2021, 1, 1, tzinfo=timezone.utc)
        )
        admin = Admin(user_id=42, target_chat=target_chat)

        admin_repository = PostgresAdminRepository(db_connection)
        await admin_repository.add(admin)

        target_chat_row = await db_connection.fetchrow(
            """
            SELECT
                chat_id, created_at
            FROM
                target_chat
            WHERE chat_id = $1
            """,
            target_chat.chat_id
        )
        assert target_chat_row["chat_id"] == target_chat.chat_id
        assert target_chat_row["created_at"] == target_chat.created_at

        admin_row = await db_connection.fetchrow(
            """
            SELECT
                user_id, target_chat_id
            FROM
                admin
            WHERE user_id = $1
            """,
            admin.user_id
        )
        assert admin_row["user_id"] == admin.user_id
        assert admin_row["target_chat_id"] == admin.target_chat.chat_id
