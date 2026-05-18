from aiogram import F, Router
from aiogram.types import CallbackQuery

from database.models import User

from .keyboards import profile_keyboard
from .texts import profile_text

router = Router()


@router.callback_query(F.data == "profile")
async def profile_handler(
    callback: CallbackQuery,
    user: User,
) -> None:
    await callback.message.edit_text(
        profile_text(user),
        reply_markup=profile_keyboard(),
    )

    await callback.answer()