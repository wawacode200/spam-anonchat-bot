from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from database.repositories.users import UsersRepository

from .filters import AdminFilter
from .keyboards import admin_back_keyboard, admin_keyboard
from .texts import ADMIN_TEXT, admin_stats_text

router = Router()

router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())


@router.message(Command("admin"))
async def admin_handler(message: Message) -> None:
    await message.answer(
        ADMIN_TEXT,
        reply_markup=admin_keyboard(),
    )


@router.callback_query(F.data == "admin:menu")
async def admin_menu_handler(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        ADMIN_TEXT,
        reply_markup=admin_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "admin:stats")
async def admin_stats_handler(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    users_repo = UsersRepository(session)
    users_count = await users_repo.count_all()

    await callback.message.edit_text(
        admin_stats_text(users_count),
        reply_markup=admin_back_keyboard(),
    )

    await callback.answer()