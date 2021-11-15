from datetime import datetime, timezone

import asyncpg
import pytest

from feedback_bot.adapters.repositories.admin import PostgresAdminRepository
from feedback_bot.adapters.repositories.forwarded_message import (
    PostgresForwardedMessageRepository
)
from feedback_bot.adapters.repositories.target_chat import PostgresTargetChatRepository
from feedback_bot.model import Admin, ForwardedMessage, TargetChat


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


class TestPostgresTargetChatRepository:
    @pytest.mark.asyncio
    async def test_target_chat_repository_get(self, db_connection: asyncpg.Connection):
        target_chat_id = 42
        target_chat_created_at = datetime(2021, 1, 1, tzinfo=timezone.utc)
        await db_connection.executemany(
            """
            INSERT INTO target_chat (chat_id, created_at)
            VALUES ($1, $2)
            """,
            [
                (target_chat_id, target_chat_created_at),
                (13, datetime(2020, 1, 2, tzinfo=timezone.utc)),
                (37, datetime(2020, 1, 3, tzinfo=timezone.utc)),
            ]
        )

        target_chat_repository = PostgresTargetChatRepository(db_connection)
        target_chat = await target_chat_repository.get(target_chat_id)

        assert target_chat.chat_id == target_chat_id
        assert target_chat.created_at == target_chat_created_at

    @pytest.mark.asyncio
    async def test_target_chat_repository_get_not_found(self, db_connection: asyncpg.Connection):
        target_chat_repository = PostgresTargetChatRepository(db_connection)
        target_chat = await target_chat_repository.get(42)

        assert target_chat is None

    @pytest.mark.asyncio
    async def test_target_chat_repository_get_latest(
        self, db_connection: asyncpg.Connection
    ):
        latest_chat_id = 42
        latest_created_at = datetime(2021, 1, 1, tzinfo=timezone.utc)
        await db_connection.executemany(
            """
            INSERT INTO target_chat (chat_id, created_at)
            VALUES ($1, $2)
            """,
            [
                (latest_chat_id, latest_created_at),
                (13, datetime(2020, 1, 2, tzinfo=timezone.utc)),
                (37, datetime(2020, 1, 3, tzinfo=timezone.utc)),
            ]
        )

        target_chat_repository = PostgresTargetChatRepository(db_connection)
        latest_target_chat = await target_chat_repository.get_latest()

        assert latest_target_chat.chat_id == latest_chat_id
        assert latest_target_chat.created_at == latest_created_at

    @pytest.mark.asyncio
    async def test_target_chat_repository_get_latest_not_found(
        self, db_connection: asyncpg.Connection
    ):
        target_chat_repository = PostgresTargetChatRepository(db_connection)
        latest_target_chat = await target_chat_repository.get_latest()

        assert latest_target_chat is None

    @pytest.mark.asyncio
    async def test_target_chat_repository_remove(
        self, db_connection: asyncpg.Connection
    ):
        target_chat_id = 42
        target_chat_created_at = datetime(2021, 1, 1, tzinfo=timezone.utc)

        await db_connection.execute(
            """
            INSERT INTO target_chat (chat_id, created_at)
            VALUES ($1, $2)
            """,
            target_chat_id, target_chat_created_at
        )

        target_chat_repository = PostgresTargetChatRepository(db_connection)
        removed_target_chat = await target_chat_repository.remove(target_chat_id)

        assert removed_target_chat.chat_id == target_chat_id
        assert removed_target_chat.created_at == target_chat_created_at

    @pytest.mark.asyncio
    async def test_target_chat_repository_remove_not_found(
        self, db_connection: asyncpg.Connection
    ):
        target_chat_repository = PostgresTargetChatRepository(db_connection)
        removed_target_chat = await target_chat_repository.remove(42)

        assert removed_target_chat is None

    @pytest.mark.asyncio
    async def test_target_chat_repository_add(self, db_connection: asyncpg.Connection):
        target_chat = TargetChat(
            chat_id=42,
            created_at=datetime(2021, 1, 1, tzinfo=timezone.utc),
        )

        target_chat_repository = PostgresTargetChatRepository(db_connection)
        await target_chat_repository.add(target_chat)

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


class TestPostgresForwardedMessageRepository:
    @pytest.mark.asyncio
    async def test_forwarded_message_repository_get(
        self, db_connection: asyncpg.Connection
    ):
        forwarded_message_id = 42
        target_chat_id = 24
        origin_chat_id = 13
        created_at = datetime(year=2021, month=1, day=1, tzinfo=timezone.utc)

        await db_connection.executemany(
            """
            INSERT INTO forwarded_message
                (
                    forwarded_message_id,
                    target_chat_id,
                    origin_chat_id,
                    created_at
                )
            VALUES ($1, $2, $3, $4)
            """,
            [
                (13, 37, 20, datetime(year=2020, month=1, day=2)),
                (forwarded_message_id, target_chat_id, origin_chat_id, created_at),
                (42, 42, 42, datetime(year=2020, month=2, day=3)),
            ]
        )

        forwarded_message_repository = PostgresForwardedMessageRepository(
            db_connection
        )
        forwarded_message = await forwarded_message_repository.get(
            forwarded_message_id=forwarded_message_id,
            target_chat_id=target_chat_id,
        )

        assert forwarded_message.forwarded_message_id == forwarded_message_id
        assert forwarded_message.target_chat_id == target_chat_id
        assert forwarded_message.origin_chat_id == origin_chat_id
        assert forwarded_message.created_at == created_at

    @pytest.mark.asyncio
    async def test_forwarded_message_repository_get_not_found(
        self, db_connection: asyncpg.Connection
    ):
        forwarded_message_repository = PostgresForwardedMessageRepository(
            db_connection
        )
        forwarded_message = await forwarded_message_repository.get(
            forwarded_message_id=42,
            target_chat_id=24,
        )

        assert forwarded_message is None

    @pytest.mark.asyncio
    async def test_forwarded_message_repository_add(
        self, db_connection: asyncpg.Connection
    ):
        forwarded_message = ForwardedMessage(
            forwarded_message_id=13,
            target_chat_id=37,
            origin_chat_id=42,
            created_at=datetime(year=2021, month=1, day=1, tzinfo=timezone.utc),
        )

        forwarded_message_repository = PostgresForwardedMessageRepository(
            db_connection
        )
        await forwarded_message_repository.add(forwarded_message)

        forwarded_message_row = await db_connection.fetchrow(
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
            forwarded_message.forwarded_message_id,
            forwarded_message.target_chat_id,
        )
        assert (
            forwarded_message_row["forwarded_message_id"]
            == forwarded_message.forwarded_message_id
        )
        assert (
            forwarded_message_row["target_chat_id"]
            == forwarded_message.target_chat_id
        )
        assert (
            forwarded_message_row["origin_chat_id"]
            == forwarded_message.origin_chat_id
        )
        assert (
            forwarded_message_row["created_at"]
            == forwarded_message.created_at
        )
