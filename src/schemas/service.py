import datetime
import uuid

from pydantic import BaseModel


class ServiceCreate(BaseModel):
    name: str
    category: str
    duration_minutes: int
    requires_lift: bool = False
    description: str | None = None


class ServiceRead(BaseModel):
    id: uuid.UUID
    name: str
    category: str
    duration_minutes: int
    requires_lift: bool
    description: str | None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
