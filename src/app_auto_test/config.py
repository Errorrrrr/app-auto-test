from functools import lru_cache
import os
from pathlib import Path

from pydantic import BaseModel, Field


class Settings(BaseModel):
    data_dir: Path = Field(default=Path(".local-data"))
    adb_path: str = Field(default="/Users/zxx/Library/Android/sdk/platform-tools/adb")
    maestro_bin: str = Field(default="maestro")
    allow_real_execution: bool = Field(default=False)


def _as_bool(value: str | None) -> bool:
    if value is None:
        return False
    return value.strip().lower() in {"1", "true", "yes", "on"}


@lru_cache
def get_settings() -> Settings:
    return Settings(
        data_dir=Path(os.getenv("APP_AUTO_TEST_DATA_DIR", ".local-data")),
        adb_path=os.getenv(
            "APP_AUTO_TEST_ADB_PATH",
            "/Users/zxx/Library/Android/sdk/platform-tools/adb",
        ),
        maestro_bin=os.getenv("APP_AUTO_TEST_MAESTRO_BIN", "maestro"),
        allow_real_execution=_as_bool(os.getenv("APP_AUTO_TEST_ALLOW_REAL_EXECUTION")),
    )

