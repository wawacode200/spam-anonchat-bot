from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TelegramUser

from config import settings


class AdminMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        telegram_user: TelegramUser | None = data.get("event_from_user")

        data["is_admin"] = (
            telegram_user is not None
            and telegram_user.id in settings.ADMINS
        )

        return await handler(event, data)