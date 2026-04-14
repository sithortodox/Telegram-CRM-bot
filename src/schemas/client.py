import datetime
import uuid

from pydantic import BaseModel, Field


class ClientCreate(BaseModel):
    telegram_id: int
    username: str | None = None
    full_name: str
    phone: str
    data_consent: bool = False


class ClientRead(BaseModel):
    id: uuid.UUID
    telegram_id: int
    username: str | None
    full_name: str
    phone: str
    data_consent: bool
    data_consent_at: datetime.datetime | None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class ClientUpdate(BaseModel):
    full_name: str | None = None
    phone: str | None = None
