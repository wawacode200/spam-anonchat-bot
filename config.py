from dataclasses import dataclass
from os import getenv

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    BOT_TOKEN: str
    ADMINS: list[int]
    DATABASE_URL: str


def parse_admins(value: str | None) -> list[int]:
    if not value:
        return []

    return [
        int(admin_id.strip())
        for admin_id in value.split(",")
        if admin_id.strip()
    ]


settings = Settings(
    BOT_TOKEN=getenv("BOT_TOKEN", ""),
    ADMINS=parse_admins(getenv("ADMINS")),
    DATABASE_URL=getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///database/bot.db",
    ),
)