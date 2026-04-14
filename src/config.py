import enum
from datetime import time
from typing import Self

from pydantic_settings import BaseSettings, SettingsConfigDict


class RoleEnum(str, enum.Enum):
    OWNER = "owner"
    ADMIN = "admin"
    MANAGER = "manager"
    MASTER = "master"
    MARKETING = "marketing"


class AppointmentStatusEnum(str, enum.Enum):
    CREATED = "created"
    CONFIRMED = "confirmed"
    REMINDER_SENT_DAY_BEFORE = "reminder_sent_day_before"
    REMINDER_SENT_2H_BEFORE = "reminder_sent_2h_before"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED_BY_CLIENT = "cancelled_by_client"
    CANCELLED_BY_ADMIN = "cancelled_by_admin"
    RESCHEDULED = "rescheduled"
    NO_SHOW = "no_show"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Telegram
    bot_token: str

    # База данных
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "crm_autoservice"
    db_user: str = "postgres"
    db_password: str = "postgres"

    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0

    # FastAPI
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Логирование
    log_level: str = "INFO"

    # ID владельцев
    owner_ids: str = ""

    # График работы
    work_start: str = "09:00"
    work_end: str = "21:00"
    work_days: str = "0,1,2,3,4,5"

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def database_url_sync(self) -> str:
        return (
            f"postgresql://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def redis_url(self) -> str:
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"

    @property
    def work_start_time(self) -> time:
        parts = self.work_start.split(":")
        return time(int(parts[0]), int(parts[1]))

    @property
    def work_end_time(self) -> time:
        parts = self.work_end.split(":")
        return time(int(parts[0]), int(parts[1]))

    @property
    def work_days_list(self) -> list[int]:
        return [int(d.strip()) for d in self.work_days.split(",") if d.strip()]

    @property
    def owner_ids_list(self) -> list[int]:
        if not self.owner_ids:
            return []
        return [int(uid.strip()) for uid in self.owner_ids.split(",") if uid.strip()]

    @classmethod
    def load(cls) -> Self:
        return cls()


settings = Settings.load()
