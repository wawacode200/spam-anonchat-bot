from aiogram import Dispatcher

from features.broadcast.router import router as broadcast_router
from features.sessions.router import router as sessions_router

def setup_routers(dp: Dispatcher) -> None:
    dp.include_router(broadcast_router)
    dp.include_router(sessions_router)