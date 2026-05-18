from aiogram.types import User as TelegramUser
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import User


class UsersRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, user_id: int) -> User | None:
        result = await self.session.execute(
            select(User).where(User.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        telegram_user: TelegramUser,
    ) -> User:
        user = await self.get_by_id(telegram_user.id)

        if user:
            user.username = telegram_user.username
            user.full_name = telegram_user.full_name
            return user

        user = User(
            user_id=telegram_user.id,
            username=telegram_user.username,
            full_name=telegram_user.full_name,
        )

        self.session.add(user)

        return user

    async def count_all(self) -> int:
        result = await self.session.execute(
            select(func.count(User.user_id))
        )
        return result.scalar_one()