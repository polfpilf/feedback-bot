import pytest

from feedback_bot.model import Admin, ForwardedMessage, TargetChat


class TestTargetChat:
    def test_target_chat_eq(self):
        target_chat_1 = TargetChat(chat_id=42)
        target_chat_2 = TargetChat(chat_id=42)

        assert target_chat_1 == target_chat_2

    def test_target_chat_neq(self):
        target_chat_1 = TargetChat(chat_id=13)
        target_chat_2 = TargetChat(chat_id=37)

        assert target_chat_1 != target_chat_2


class TestAdmin:
    def test_admin_eq(self):
        target_chat = TargetChat(chat_id=42)
        admin_1 = Admin(user_id=13, target_chat=target_chat)
        admin_2 = Admin(user_id=13, target_chat=target_chat)

        assert admin_1 == admin_2

    def test_admin_neq(self):
        target_chat = TargetChat(chat_id=42)
        admin_1 = Admin(user_id=13, target_chat=target_chat)
        admin_2 = Admin(user_id=37, target_chat=target_chat)

        assert admin_1 != admin_2

    def test_admin_authentication_failure(self):
        user_token = "spam"
        admin_token = "eggs"

        res = Admin.authenticate(
            user_id=42,
            chat_id=13,
            token=user_token,
            admin_token=admin_token,
        )
        assert res is None

    def test_admin_authentication_success(self):
        user_token = admin_token = "spam"
        user_id = 42
        chat_id = 13

        res = Admin.authenticate(
            user_id=user_id,
            chat_id=chat_id,
            token=user_token,
            admin_token=admin_token,
        )
        assert res.user_id == user_id
        assert res.target_chat.chat_id == chat_id


class TestForwardedMessage:
    @pytest.mark.parametrize(
        ("msg_1", "msg_2"),
        [
            pytest.param(
                ForwardedMessage(
                    forwarded_message_id=100,
                    target_chat_id=1,
                    origin_chat_id=1,
                ),
                ForwardedMessage(
                    forwarded_message_id=100,
                    target_chat_id=2,
                    origin_chat_id=1,
                ),
                id="same message ID, different target chats"
            ),
            pytest.param(
                ForwardedMessage(
                    forwarded_message_id=100,
                    target_chat_id=1,
                    origin_chat_id=1,
                ),
                ForwardedMessage(
                    forwarded_message_id=100,
                    target_chat_id=2,
                    origin_chat_id=1,
                ),
                id="same target chat, different message IDs"
            ),
        ]
    )
    def test_forwarded_message_neq(self, msg_1: ForwardedMessage, msg_2: ForwardedMessage):
        assert msg_1 != msg_2

    def test_forwarded_message_eq(self):
        msg_1 = ForwardedMessage(
            forwarded_message_id=42,
            target_chat_id=13,
            origin_chat_id=37,
        )
        msg_2 = ForwardedMessage(
            forwarded_message_id=42,
            target_chat_id=13,
            origin_chat_id=37,
        )

        assert msg_1 == msg_2
