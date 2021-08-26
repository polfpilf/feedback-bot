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

        self.telegram_api = FakeTelegramAPI()
        self.admin_repository = InMemoryAdminRepository(admins=admins, target_chats=target_chats)
        self.target_chat_repository = InMemoryTargetChatRepository(target_chats=target_chats)
        self.forwarded_message_repository = InMemoryForwardedMessageRepository(
            forwarded_messages=forwarded_messages
        )
    
    async def rollback(self):
        self.rolled_back = True

    async def commit(self):
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
    async def test_authenticate_admin_failure(
        self, mock_uow: InMemoryUnitOfWork, mock_admin_token: str,
    ):
        user_id = 42
        token = "spam"
        
        await services.authenticate_admin(user_id=user_id, chat_id=13, token=token)
        
        admin = await mock_uow.admin_repository.get(user_id)
        assert admin is None
        assert not mock_uow.telegram_api.sent_messages

    @pytest.mark.asyncio
    async def test_authenticate_admin_success(
        self, mock_uow: InMemoryUnitOfWork, mock_admin_token: str,
    ):
        user_id = 42
        chat_id = 13
        token = mock_admin_token

        await services.authenticate_admin(
            user_id=user_id, chat_id=chat_id, token=token
        )

        admin = await mock_uow.admin_repository.get(user_id)
        assert admin.user_id == user_id
        assert mock_uow.commited
        assert mock_uow.telegram_api.sent_messages == [
            FakeSentMessage(
                to_chat_id=chat_id,
                text="Auth token successfully verified",
            ),
        ]


class TestAddGroup:
    @pytest.mark.asyncio
    async def test_add_group_no_admins(self, mock_uow: InMemoryUnitOfWork):
        group_chat_id = 1337

        await services.add_group(by_user_id=42, group_chat_id=group_chat_id)

        target_chat = await mock_uow.target_chat_repository.get(group_chat_id)
        assert target_chat is None
        assert not mock_uow.telegram_api.sent_messages

    @pytest.mark.asyncio
    async def test_add_group_not_admin(self, mock_uow: InMemoryUnitOfWork):
        group_chat_id = 1337
        added_by_user_id = 13
        admin = Admin(user_id=37, target_chat=TargetChat(chat_id=42))
        await mock_uow.admin_repository.add(admin)
        
        await services.add_group(by_user_id=added_by_user_id, group_chat_id=group_chat_id)

        target_chat = await mock_uow.target_chat_repository.get(group_chat_id)
        assert target_chat is None
        assert not mock_uow.telegram_api.sent_messages

    @pytest.mark.asyncio
    async def test_add_group_success(self, mock_uow: InMemoryUnitOfWork):
        group_chat_id = 1337
        added_by_user_id = 13

        admin_1_chat = TargetChat(chat_id=42)
        admin_2_chat = TargetChat(chat_id=24)
        admin_1 = Admin(user_id=added_by_user_id, target_chat=admin_1_chat)
        admin_2 = Admin(user_id=420, target_chat=admin_2_chat)
        await mock_uow.admin_repository.add(admin_1)
        await mock_uow.admin_repository.add(admin_2)

        await services.add_group(by_user_id=added_by_user_id, group_chat_id=group_chat_id)

        target_chat = await mock_uow.target_chat_repository.get(group_chat_id)
        assert target_chat.chat_id == group_chat_id
        assert mock_uow.commited

        message_text = f"Group chat {group_chat_id} added"
        assert set(mock_uow.telegram_api.sent_messages) == {
            FakeSentMessage(to_chat_id=admin_1_chat.chat_id, text=message_text),
            FakeSentMessage(to_chat_id=admin_2_chat.chat_id, text=message_text),
        }


class TestRemoveGroup:
    @pytest.mark.asyncio
    async def test_remove_group_non_existent(self, mock_uow: InMemoryUnitOfWork):
        removed_group_chat_id = 13

        existing_target_chat = TargetChat(chat_id=37)
        await mock_uow.target_chat_repository.add(existing_target_chat)

        await services.remove_group(group_chat_id=removed_group_chat_id)

        target_chat_after_remove = await mock_uow.target_chat_repository.get(
            existing_target_chat.chat_id
        )
        assert target_chat_after_remove == existing_target_chat

        assert not mock_uow.telegram_api.sent_messages

    @pytest.mark.asyncio
    async def test_remove_group_success(self, mock_uow: InMemoryUnitOfWork):
        removed_group_chat_id = 13
        existing_target_chat = TargetChat(chat_id=removed_group_chat_id)
        await mock_uow.target_chat_repository.add(existing_target_chat)

        admin_1_chat = TargetChat(chat_id=42)
        admin_2_chat = TargetChat(chat_id=24)
        admin_1 = Admin(user_id=1337, target_chat=admin_1_chat)
        admin_2 = Admin(user_id=420, target_chat=admin_2_chat)
        await mock_uow.admin_repository.add(admin_1)
        await mock_uow.admin_repository.add(admin_2)

        await services.remove_group(group_chat_id=removed_group_chat_id)

        target_chat_after_remove = await mock_uow.target_chat_repository.get(
            removed_group_chat_id
        )
        assert target_chat_after_remove is None
        assert mock_uow.commited

        message_text = f"Group chat {removed_group_chat_id} removed"
        assert set(mock_uow.telegram_api.sent_messages) == {
            FakeSentMessage(to_chat_id=admin_1_chat.chat_id, text=message_text),
            FakeSentMessage(to_chat_id=admin_2_chat.chat_id, text=message_text),
        }


class TestForwardIncomingMessage:
    @pytest.mark.asyncio
    async def test_forward_incoming_message_no_target_chats(
        self, mock_uow: InMemoryUnitOfWork
    ):
        await services.forward_incoming_message(origin_chat_id=13, message_id=37)

        assert not mock_uow.telegram_api.forwarded_messages
        messages = await mock_uow.forwarded_message_repository.get_all()
        assert not messages

    @pytest.mark.asyncio
    async def test_forward_incoming_message_success(
        self, mock_uow: InMemoryUnitOfWork
    ):
        origin_chat_id = 42
        message_id = 24
    
        # latest chat, should be selected as target
        target_chat_1 = TargetChat(chat_id=13, created_at=datetime(2021, 2, 2))
        target_chat_2 = TargetChat(chat_id=37, created_at=datetime(2020, 1, 1))
        await mock_uow.target_chat_repository.add(target_chat_1)
        await mock_uow.target_chat_repository.add(target_chat_2)

        await services.forward_incoming_message(
            origin_chat_id=origin_chat_id, message_id=message_id
        )

        forwarded_message = await mock_uow.forwarded_message_repository.get(
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


class TestForwardReply:
    @pytest.mark.asyncio
    async def test_forward_reply_not_forwarded_message(
        self, mock_uow: InMemoryUnitOfWork
    ):
        forwarded_message = ForwardedMessage(
            forwarded_message_id=13,
            target_chat_id=37,
            origin_chat_id=42,
        )
        await mock_uow.forwarded_message_repository.add(forwarded_message)

        await services.forward_reply(
            target_chat_id=1337,
            forwarded_message_id=420,
            reply_message_id=100,
        )

        assert not mock_uow.telegram_api.copied_messages

    @pytest.mark.asyncio
    async def test_forward_reply_success(self, mock_uow: InMemoryUnitOfWork):
        forwarded_message_id = 13
        target_chat_id = 37
        origin_chat_id = 42
        reply_message_id = 100

        forwarded_message = ForwardedMessage(
            forwarded_message_id=forwarded_message_id,
            target_chat_id=target_chat_id,
            origin_chat_id=origin_chat_id,
        )
        await mock_uow.forwarded_message_repository.add(forwarded_message)

        await services.forward_reply(
            target_chat_id=target_chat_id,
            forwarded_message_id=forwarded_message_id,
            reply_message_id=reply_message_id,
        )

        assert mock_uow.telegram_api.copied_messages == [
            FakeCopiedMessage(
                from_chat_id=target_chat_id,
                to_chat_id=origin_chat_id,
                message_id=reply_message_id,
            )
        ]
