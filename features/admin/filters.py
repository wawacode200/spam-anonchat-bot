from aiogram.filters import BaseFilter
from aiogram.types import CallbackQuery, Message


class AdminFilter(BaseFilter):
    async def __call__(
        self,
        event: Message | CallbackQuery,
        is_admin: bool,
    ) -> bool:
        return is_admin