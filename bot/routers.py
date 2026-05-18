from aiogram import Dispatcher

from features.admin.router import router as admin_router
from features.start.router import router as start_router
from features.profile.router import router as profile_router


def setup_routers(dp: Dispatcher) -> None:
    dp.include_router(admin_router)
    dp.include_router(start_router)
    dp.include_router(profile_router)