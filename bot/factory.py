from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.routers import setup_routers
from config import settings
from database.session import async_session_maker
from middlewares.db import DbSessionMiddleware
from middlewares.user import UserMiddleware
from middlewares.admin import AdminMiddleware

def create_bot() -> Bot:
    if not settings.BOT_TOKEN:
        raise RuntimeError("BOT_TOKEN is empty. Check your .env file.")

    return Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def create_dispatcher() -> Dispatcher:
    dp = Dispatcher()

    dp.update.middleware(
        DbSessionMiddleware(async_session_maker)
    )

    dp.update.middleware(
        UserMiddleware()
    )

    dp.update.middleware(
        AdminMiddleware()
    )

    setup_routers(dp)

    return dp