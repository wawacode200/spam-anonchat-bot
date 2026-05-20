from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from database.models import TelethonSessionState


class TelethonSessionsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_map(self) -> dict[str, TelethonSessionState]:
        result = await self.session.execute(
            select(TelethonSessionState)
        )

        return {
            state.name: state
            for state in result.scalars().all()
        }

    async def upsert(
        self,
        name: str,
        status: str,
        available_at: datetime | None,
        last_error: str | None,
    ) -> None:
        state = await self.session.get(
            TelethonSessionState,
            name,
        )

        if state is None:
            state = TelethonSessionState(name=name)
            self.session.add(state)

        state.status = status
        state.available_at = available_at
        state.last_error = last_error

    async def reset_all(self) -> int:
        result = await self.session.execute(
            update(TelethonSessionState)
            .values(
                status="active",
                available_at=None,
                last_error=None,
            )
        )

        return result.rowcount or 0

    async def count_all(self) -> int:
        result = await self.session.execute(
            select(func.count()).select_from(TelethonSessionState)
        )

        return result.scalar_one()
