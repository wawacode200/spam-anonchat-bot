from datetime import datetime

from sqlalchemy import BigInteger, DateTime, String
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