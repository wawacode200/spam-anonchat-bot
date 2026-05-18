from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from config import settings
from database.base import Base
from database import models  # noqa: F401


engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
)

async_session_maker = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)