from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from common.time import now_msk
from database.base import Base


class User(Base):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, )
    username: Mapped[str | None] = mapped_column(String(64), nullable=True, )
    full_name: Mapped[str] = mapped_column(String(128), nullable=False, )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_msk,
    )


class BroadcastSettings(Base):
    __tablename__ = "broadcast_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    batch_size: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    interval: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    broadcast_text: Mapped[str] = mapped_column(Text, nullable=False)


class TelethonSessionState(Base):
    __tablename__ = "telethon_session_states"

    name: Mapped[str] = mapped_column(String(255), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="active")
    available_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_error: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=now_msk,
        onupdate=now_msk,
    )
