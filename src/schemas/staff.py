import datetime
import uuid

from pydantic import BaseModel

from src.config import RoleEnum


class StaffCreate(BaseModel):
    telegram_id: int | None = None
    full_name: str
    role: RoleEnum = RoleEnum.MASTER
    phone: str | None = None
    specializations: str | None = None


class StaffRead(BaseModel):
    id: uuid.UUID
    telegram_id: int | None
    full_name: str
    role: str
    phone: str | None
    specializations: str | None
    is_active: bool
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class StaffUpdate(BaseModel):
    full_name: str | None = None
    role: str | None = None
    phone: str | None = None
    specializations: str | None = None
    is_active: bool | None = None
