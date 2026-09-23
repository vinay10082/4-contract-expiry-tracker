"""Runtime configuration sourced from environment variables (and an optional .env file)."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    sqlite_db_path: str
    expiry_warning_threshold_days: int


def load_config() -> Config:
    load_dotenv()
    db_path = os.environ.get("SQLITE_DB_PATH", "contracts.db")
    threshold_raw = os.environ.get("EXPIRY_WARNING_THRESHOLD_DAYS", "30")
    try:
        threshold = int(threshold_raw)
    except ValueError:
        raise ValueError(
            f"EXPIRY_WARNING_THRESHOLD_DAYS must be an integer, got {threshold_raw!r}"
        )
    return Config(sqlite_db_path=db_path, expiry_warning_threshold_days=threshold)
