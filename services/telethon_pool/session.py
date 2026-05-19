from dataclasses import dataclass
from datetime import datetime


@dataclass
class PoolSession:
    name: str
    status: str = "active"
    available_at: datetime | None = None
    last_error: str | None = None