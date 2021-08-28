from datetime import datetime
from typing import Dict, List, NamedTuple, Optional, Tuple

import pytest
from dependency_injector import providers

from feedback_bot.adapters.repositories.admin import AbstractAdminRepository
from feedback_bot.adapters.repositories.forwarded_message import (
    AbstractForwardedMessageRepository
)
from feedback_bot.adapters.repositories.target_chat import AbstractTargetChatRepository
from feedback_bot.adapters.telegram import AbstractTelegramAPI
from feedback_bot.model import Admin, ForwardedMessage, TargetChat
from feedback_bot.service_layer import services
from feedback_bot.service_layer.unit_of_work import AbstractUnitOfWork


class InMemoryAdminRepository(AbstractAdminRepository):
    def __init__(self, admins: Dict[int, Admin], target_chats: Dict[int, TargetChat]):
        self._admins = admins
        self._target_chats = target_chats 
    
    async def get(self, user_id: int):
        return self._admins.get(user_id)

    async def get_all(self):
        return list(self._admins.values())
    
    async def add(self, admin: Admin):
        self._admins[admin.user_id] = admin
        self._target_chats[admin.target_chat.chat_id] = admin.target_chat


class InMemoryForwardedMessageRepository(AbstractForwardedMessageRepository):
    def __init__(self, forwarded_messages: Dict[Tuple[int, int], ForwardedMessage]):
        self._forwarded_messages = forwarded_messages

    async def get(self, forwarded_message_id: int, target_chat_id: int):
        key = (forwarded_message_id, target_chat_id)
        return self._forwarded_messages.get(key)

    async def get_all(self):
        return list(self._forwarded_messages.values())

    async def add(self, forwarded_message: ForwardedMessage):
        key = (forwarded_message.forwarded_message_id, forwarded_message.target_chat_id)
        self._forwarded_messages[key] = forwarded_message


class InMemoryTargetChatRepository(AbstractTargetChatRepository):
    def __init__(self, target_chats: Dict[int, TargetChat]):
        self._target_chats = target_chats

    async def get(self, chat_id: int) -> Optional[TargetChat]:
        return self._target_chats.get(chat_id)

    async def get_latest(self):
        return max(
            self._target_chats.values(),
            key=lambda group: group.created_at,
            default=None,
        )
    
    async def remove(self, chat_id: int):
        return self._target_chats.pop(chat_id, None)
    
    async def add(self, target_chat: TargetChat):
        self._target_chats[target_chat.chat_id] = target_chat


class FakeSentMessage(NamedTuple):
    to_chat_id: int
    text: str


class FakeForwardedMessage(NamedTuple):
    from_chat_id: int
    to_chat_id: int
    message_id: int


class FakeCopiedMessage(NamedTuple):
    from_chat_id: int
    to_chat_id: int
    message_id: int


class FakeTelegramAPI(AbstractTelegramAPI):
    FAKE_FORWARDED_MESSAGE_ID = 42

    def __init__(self):
        self.sent_messages: List[FakeSentMessage] = []
        self.forwarded_messages: List[FakeForwardedMessage] = []
        self.copied_messages: List[FakeCopiedMessage] = []
    
    async def send_message(self, to_chat_id: int, text: str):
        self.sent_messages.append(FakeSentMessage(to_chat_id=to_chat_id, text=text))

    async def forward_message(
        self, from_chat_id: int, to_chat_id: int, message_id: int
    ):
        self.forwarded_messages.append(
            FakeForwardedMessage(
                from_chat_id=from_chat_id,
                to_chat_id=to_chat_id,
                message_id=message_id
            )
        )
        return self.FAKE_FORWARDED_MESSAGE_ID

    async def copy_message(
        self, from_chat_id: int, to_chat_id: int, message_id: int
    ):
        self.copied_messages.append(
            FakeCopiedMessage(
                from_chat_id=from_chat_id, to_chat_id=to_chat_id, message_id=message_id
            )
        )


class InMemoryUnitOfWork(AbstractUnitOfWork):
    target_chat_repository: InMemoryTargetChatRepository
    telegram_api: FakeTelegramAPI

    commited: bool
    rolled_back: bool

    def __init__(
        self,
        admins: Dict[int, Admin],
        target_chats: Dict[int, TargetChat],
        forwarded_messages: Dict[Tuple[int, int], ForwardedMessage],
    ):
        self.commited = False
        self.rolled_back = False

        self.admins = InMemoryAdminRepository(admins=admins, target_chats=target_chats)
        self.target_chats = InMemoryTargetChatRepository(target_chats=target_chats)
        self.forwarded_messages = InMemoryForwardedMessageRepository(
            forwarded_messages=forwarded_messages
        )
        self.telegram_api = FakeTelegramAPI()
    
    async def _rollback(self):
        self.rolled_back = True

    async def _commit(self):
        self.commited = True


@pytest.fixture
def mock_uow(container):
    admins = {}
    target_chats = {}
    forwarded_messages = {}
    uow = InMemoryUnitOfWork(
        admins=admins,
        target_chats=target_chats,
        forwarded_messages=forwarded_messages,
    )

    with container.uow.override(uow):
        yield uow


@pytest.fixture
def mock_admin_token(container):
    admin_token = "admin_token"
    with container.config.ADMIN_TOKEN.override(admin_token):
        yield admin_token


class TestAuthenticateAdmin:
    @pytest.mark.asyncio
    async def test_authenticate_admin_wrong_password_no_admin_created(
        self, mock_uow: InMemoryUnitOfWork, mock_admin_token: str,
    ):
        """Admin should not be created if provided password is wrong."""
    
        user_id = 42
        token = "spam"
        
        await services.authenticate_admin(user_id=user_id, chat_id=13, token=token)
        
        admin = await mock_uow.admins.get(user_id)
        assert admin is None
        assert not mock_uow.telegram_api.sent_messages

    @pytest.mark.asyncio
    async def test_authenticate_admin_correct_password_admin_created(
        self, mock_uow: InMemoryUnitOfWork, mock_admin_token: str,
    ):
        """Admin should be created if provided password is correct."""
    
        user_id = 42
        chat_id = 13
        token = mock_admin_token

        await services.authenticate_admin(
            user_id=user_id, chat_id=chat_id, token=token
        )

        admin = await mock_uow.admins.get(user_id)
        assert admin.user_id == user_id
        assert mock_uow.commited
        assert mock_uow.telegram_api.sent_messages == [
            FakeSentMessage(
                to_chat_id=chat_id,
                text="Auth token successfully verified",
            ),
        ]

    @pytest.mark.asyncio
    async def test_authenticate_admin_already_authenticated_ignored(
        self, mock_uow: InMemoryUnitOfWork
    ):
        """If Admin already exists, ignore the command."""

        target_chat = TargetChat(chat_id=13)
        admin = Admin(user_id=37, target_chat=target_chat)
        await mock_uow.admins.add(admin)

        await services.authenticate_admin(
            user_id=admin.user_id,
            chat_id=target_chat.chat_id,
            token="spam",
            admin_token="spam",
        )

        admin_after_auth = await mock_uow.admins.get(admin.user_id)
        assert admin == admin_after_auth
        assert not mock_uow.telegram_api.sent_messages


class TestAddGroup:
    @pytest.mark.asyncio
    async def test_add_group_no_admins_ignored(self, mock_uow: InMemoryUnitOfWork):
        """If no Admins exist, adding bot to a group should be ignored."""

        group_chat_id = 1337
        await services.add_group(by_user_id=42, group_chat_id=group_chat_id)

        target_chat = await mock_uow.target_chats.get(group_chat_id)
        assert target_chat is None
        assert not mock_uow.telegram_api.sent_messages

    @pytest.mark.asyncio
    async def test_add_group_not_admin_ignored(self, mock_uow: InMemoryUnitOfWork):
        """Adding bot to a group by non-Admin should be ignored."""
        
        group_chat_id = 1337
        added_by_user_id = 13
        admin = Admin(user_id=37, target_chat=TargetChat(chat_id=42))
        await mock_uow.admins.add(admin)
        
        await services.add_group(by_user_id=added_by_user_id, group_chat_id=group_chat_id)

        target_chat = await mock_uow.target_chats.get(group_chat_id)
        assert target_chat is None
        assert not mock_uow.telegram_api.sent_messages

    @pytest.mark.asyncio
    async def test_add_group_by_admin_save_target_chat(self, mock_uow: InMemoryUnitOfWork):
        """Adding bot to a group by Admin should create a TargetChat for the group."""

        group_chat_id = 1337
        added_by_user_id = 13

        admin_1_chat = TargetChat(chat_id=42)
        admin_2_chat = TargetChat(chat_id=24)
        admin_1 = Admin(user_id=added_by_user_id, target_chat=admin_1_chat)
        admin_2 = Admin(user_id=420, target_chat=admin_2_chat)
        await mock_uow.admins.add(admin_1)
        await mock_uow.admins.add(admin_2)

        await services.add_group(by_user_id=added_by_user_id, group_chat_id=group_chat_id)

        target_chat = await mock_uow.target_chats.get(group_chat_id)
        assert target_chat.chat_id == group_chat_id
        assert mock_uow.commited

        message_text = f"Group chat {group_chat_id} added"
        assert set(mock_uow.telegram_api.sent_messages) == {
            FakeSentMessage(to_chat_id=admin_1_chat.chat_id, text=message_text),
            FakeSentMessage(to_chat_id=admin_2_chat.chat_id, text=message_text),
        }


class TestRemoveGroup:
    @pytest.mark.asyncio
    async def test_remove_group_non_existent_ignored(self, mock_uow: InMemoryUnitOfWork):
        """Removing bot from group for which there is no TargetChat
        should be ignored.
        """

        removed_group_chat_id = 13

        existing_target_chat = TargetChat(chat_id=37)
        await mock_uow.target_chats.add(existing_target_chat)

        await services.remove_group(group_chat_id=removed_group_chat_id)

        target_chat_after_remove = await mock_uow.target_chats.get(
            existing_target_chat.chat_id
        )
        assert target_chat_after_remove == existing_target_chat

        assert not mock_uow.telegram_api.sent_messages

    @pytest.mark.asyncio
    async def test_remove_group_existing_target_chat_removed(self, mock_uow: InMemoryUnitOfWork):
        """Removing bot from a TargetChat-group
        should remove the group's TargetChat.
        """
    
        removed_group_chat_id = 13
        existing_target_chat = TargetChat(chat_id=removed_group_chat_id)
        await mock_uow.target_chats.add(existing_target_chat)

        admin_1_chat = TargetChat(chat_id=42)
        admin_2_chat = TargetChat(chat_id=24)
        admin_1 = Admin(user_id=1337, target_chat=admin_1_chat)
        admin_2 = Admin(user_id=420, target_chat=admin_2_chat)
        await mock_uow.admins.add(admin_1)
        await mock_uow.admins.add(admin_2)

        await services.remove_group(group_chat_id=removed_group_chat_id)

        target_chat_after_remove = await mock_uow.target_chats.get(
            removed_group_chat_id
        )
        assert target_chat_after_remove is None
        assert mock_uow.commited

        message_text = f"Group chat {removed_group_chat_id} removed"
        assert set(mock_uow.telegram_api.sent_messages) == {
            FakeSentMessage(to_chat_id=admin_1_chat.chat_id, text=message_text),
            FakeSentMessage(to_chat_id=admin_2_chat.chat_id, text=message_text),
        }


class TestProcessPrivateMessage:
    @pytest.mark.asyncio
    async def test_process_private_message_no_target_chats_ignored(
        self, mock_uow: InMemoryUnitOfWork
    ):
        """Private message should be ignored if there are no TargetChats."""

        await services.process_private_message(chat_id=13, message_id=37)

        assert not mock_uow.telegram_api.forwarded_messages
        messages = await mock_uow.forwarded_messages.get_all()
        assert not messages

    @pytest.mark.asyncio
    async def test_process_private_message_forwarded_to_latest_target_chat(
        self, mock_uow: InMemoryUnitOfWork
    ):
        """Private message should be forwarded to the latest TargetChat."""

        origin_chat_id = 42
        message_id = 24

        # latest chat, should be selected as target
        target_chat_1 = TargetChat(chat_id=13, created_at=datetime(2021, 2, 2))
        target_chat_2 = TargetChat(chat_id=37, created_at=datetime(2020, 1, 1))
        await mock_uow.target_chats.add(target_chat_1)
        await mock_uow.target_chats.add(target_chat_2)

        await services.process_private_message(
            chat_id=origin_chat_id, message_id=message_id
        )

        forwarded_message = await mock_uow.forwarded_messages.get(
            forwarded_message_id=mock_uow.telegram_api.FAKE_FORWARDED_MESSAGE_ID,
            target_chat_id=target_chat_1.chat_id,
        )
        assert forwarded_message.target_chat_id == target_chat_1.chat_id
        assert (
            forwarded_message.forwarded_message_id
            == mock_uow.telegram_api.FAKE_FORWARDED_MESSAGE_ID
        )
        assert forwarded_message.origin_chat_id == origin_chat_id

        assert mock_uow.commited
    
        assert mock_uow.telegram_api.forwarded_messages == [
            FakeForwardedMessage(
                from_chat_id=origin_chat_id,
                to_chat_id=target_chat_1.chat_id,
                message_id=message_id,
            )
        ]


class TestProcessReply:
    @pytest.mark.asyncio
    async def test_process_reply_not_to_forwarded_message_non_target_chat_is_forwarded(
        self, mock_uow: InMemoryUnitOfWork
    ):
        """Reply in non-TargetChats to non-ForwardedMessage
        should be forwarded to the latest TargetChat.
        """

        target_chat = TargetChat(chat_id=10)
        await mock_uow.target_chats.add(target_chat)

        await services.process_reply(
            chat_id=13,
            reply_to_message_id=37,
            message_id=42,
        )

        assert not mock_uow.telegram_api.copied_messages
        assert mock_uow.telegram_api.forwarded_messages == [
            FakeForwardedMessage(
                from_chat_id=13,
                to_chat_id=target_chat.chat_id,
                message_id=42
            )
        ]

    @pytest.mark.asyncio
    async def test_process_reply_not_to_forwarded_message_no_target_chats_ignored(
        self, mock_uow: InMemoryUnitOfWork
    ):
        """Reply should be ignored if there are no TargetChats."""

        await services.process_reply(
            chat_id=13,
            reply_to_message_id=37,
            message_id=42,
        )

        assert not mock_uow.telegram_api.copied_messages
        assert not mock_uow.telegram_api.forwarded_messages

    @pytest.mark.asyncio
    async def test_process_reply_not_to_forwarded_message_in_target_chat_ignored(
        self, mock_uow: InMemoryUnitOfWork
    ):
        """Reply to non-ForwardedMessage in TargetChat should be ignored."""

        target_chat = TargetChat(chat_id=42)
        await mock_uow.target_chats.add(target_chat)

        await services.process_reply(
            chat_id=target_chat.chat_id,
            reply_to_message_id=13,
            message_id=37,
        )

        forwarded_messages = await mock_uow.forwarded_messages.get_all()
        assert not forwarded_messages
        assert not mock_uow.telegram_api.forwarded_messages
        assert not mock_uow.telegram_api.copied_messages

    @pytest.mark.asyncio
    async def test_process_reply_to_forwarded_message_in_target_chat_copied(
        self, mock_uow: InMemoryUnitOfWork
    ):
        """Reply to ForwardedMessage in TargetChat
        should be copied to the ForwardedMessage's origin chat.
        """

        target_chat_id = 37
        forwarded_message_id = 13
        origin_chat_id = 42
        reply_message_id = 100

        forwarded_message = ForwardedMessage(
            target_chat_id=target_chat_id,
            forwarded_message_id=forwarded_message_id,
            origin_chat_id=origin_chat_id,
        )
        await mock_uow.forwarded_messages.add(forwarded_message)

        await services.process_reply(
            chat_id=target_chat_id,
            message_id=reply_message_id,
            reply_to_message_id=forwarded_message_id,
        )

        assert mock_uow.telegram_api.copied_messages == [
            FakeCopiedMessage(
                from_chat_id=target_chat_id,
                to_chat_id=origin_chat_id,
                message_id=reply_message_id,
            )
        ]
