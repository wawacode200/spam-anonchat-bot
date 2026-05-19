from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from database.models import BroadcastSettings


class BroadcastSettingsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_or_create(self) -> BroadcastSettings:
        result = await self.session.execute(
            select(BroadcastSettings).where(BroadcastSettings.id == 1)
        )
        broadcast_settings = result.scalar_one_or_none()

        if broadcast_settings:
            return broadcast_settings

        broadcast_settings = BroadcastSettings(
            id=1,
            batch_size=5,
            interval=10,
            broadcast_text=settings.BROADCAST_TEXT,
        )
        self.session.add(broadcast_settings)

        return broadcast_settings
