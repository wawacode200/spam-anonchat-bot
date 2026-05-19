from dataclasses import dataclass
from os import getenv

import socks
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    BOT_TOKEN: str
    ADMINS: list[int]
    DATABASE_URL: str
    APP_ID: int
    API_HASH: str
    PROXY: tuple | None
    BROADCAST_TEXT: str
    TARGET_CHAT_ID: str
    OPENAI_API_KEY: str


def parse_admins(value: str | None) -> list[int]:
    if not value:
        return []

    return [
        int(admin_id.strip())
        for admin_id in value.split(",")
        if admin_id.strip()
    ]


def parse_int(value: str | None, default: int = 0) -> int:
    if not value:
        return default

    return int(clean_env(value))


def clean_env(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()

    return cleaned.strip("'\"").strip()


def parse_proxy() -> tuple | None:
    host = clean_env(getenv("PROXY_HOST"))
    port = clean_env(getenv("PROXY_PORT"))

    if not host or not port:
        return None

    return (
        socks.SOCKS5,
        host,
        int(port),
        clean_env(getenv("PROXY_RDNS", "true")).lower() == "true",
        clean_env(getenv("PROXY_USERNAME")),
        clean_env(getenv("PROXY_PASSWORD")),
    )


settings = Settings(
    BOT_TOKEN=getenv("BOT_TOKEN", ""),
    ADMINS=parse_admins(getenv("ADMINS")),
    DATABASE_URL=getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///database/bot.db",
    ),
    APP_ID=parse_int(getenv("APP_ID")),
    API_HASH=getenv("API_HASH", ""),
    PROXY=parse_proxy(),
    BROADCAST_TEXT="AnonSeaChatRobot",
    TARGET_CHAT_ID=getenv("TARGET_CHAT_ID", ""),
    OPENAI_API_KEY=getenv("OPENAI_API_KEY", ""),
)
