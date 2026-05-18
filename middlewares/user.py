from collections.abc import Awaitable, Callable
from typing import Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TelegramUser

from database.repositories.users import UsersRepository


class UserMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        telegram_user: TelegramUser | None = data.get("event_from_user")

        if telegram_user is None:
            return await handler(event, data)

        session = data["session"]

        users_repo = UsersRepository(session)
        user = await users_repo.get_or_create(telegram_user)

        data["user"] = user

        return await handler(event, data)