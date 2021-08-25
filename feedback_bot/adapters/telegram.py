from abc import ABC, abstractmethod

from aiogram import Bot


class AbstractTelegramAPI(ABC):
    @abstractmethod
    async def send_message(self, to_chat_id: int, text: str):
        raise NotImplementedError

    @abstractmethod
    async def forward_message(
        self, from_chat_id: int, to_chat_id: int, message_id: int
    ) -> int:
        raise NotImplementedError

    @abstractmethod
    async def copy_message(
        self, from_chat_id: int, to_chat_id: int, message_id: int
    ):
        raise NotImplementedError


class TelegramAPI(AbstractTelegramAPI):
    def __init__(self, bot: Bot):
        self._bot = bot

    async def send_message(self, to_chat_id: int, text: str):
        await self._bot.send_message(chat_id=to_chat_id, text=text)

    async def forward_message(
        self, from_chat_id: int, to_chat_id: int, message_id: int
    ):
        tg_forwarded_message = await self._bot.forward_message(
            chat_id=to_chat_id, from_chat_id=from_chat_id, message_id=message_id
        )
        return tg_forwarded_message.message_id
    
    async def copy_message(
        self, from_chat_id: int, to_chat_id: int, message_id: int
    ):
        return await self._bot.copy_message(
            chat_id=to_chat_id, from_chat_id=from_chat_id, message_id=message_id
        )
