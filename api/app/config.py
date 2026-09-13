import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str
    redis_url: str
    kite_api_key: str | None
    kite_api_secret: str | None
    cors_origins: list[str]


def load_settings() -> Settings:
    origins = os.environ.get("CORS_ORIGINS", "https://vera-quant.onrender.com/")
    return Settings(
        database_url=os.environ.get(
            "DATABASE_URL", "postgresql+psycopg://quant:quant@localhost:5432/quant_system"
        ),
        redis_url=os.environ.get("REDIS_URL", "redis://localhost:6379/0"),
        kite_api_key=os.environ.get("KITE_API_KEY"),
        kite_api_secret=os.environ.get("KITE_API_SECRET"),
        cors_origins=[origin.strip() for origin in origins.split(",")],
    )
