import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str
    redis_url: str


def load_settings() -> Settings:
    return Settings(
        database_url=os.environ.get(
            "DATABASE_URL", "postgresql+psycopg://quant:quant@localhost:5432/quant_system"
        ),
        redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    )
