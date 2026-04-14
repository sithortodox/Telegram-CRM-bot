import datetime
import uuid

from pydantic import BaseModel

from src.config import AppointmentStatusEnum


class AppointmentCreate(BaseModel):
    client_id: uuid.UUID
    car_id: uuid.UUID
    service_id: uuid.UUID
    master_id: uuid.UUID | None = None
    lift_id: uuid.UUID | None = None
    date: datetime.date
    start_time: datetime.time
    client_comment: str | None = None


class AppointmentRead(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    car_id: uuid.UUID
    service_id: uuid.UUID
    master_id: uuid.UUID | None
    lift_id: uuid.UUID | None
    date: datetime.date
    start_time: datetime.time
    end_time: datetime.time
    status: str
    client_comment: str | None
    admin_comment: str | None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class AppointmentUpdate(BaseModel):
    master_id: uuid.UUID | None = None
    lift_id: uuid.UUID | None = None
    date: datetime.date | None = None
    start_time: datetime.time | None = None
    status: str | None = None
    admin_comment: str | None = None


class TimeSlot(BaseModel):
    start_time: datetime.time
    end_time: datetime.time
    available: bool = True
    masters_available: list[uuid.UUID] = []
    lifts_available: list[uuid.UUID] = []
