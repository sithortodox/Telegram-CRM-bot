import datetime
import uuid

from pydantic import BaseModel, Field


class CarCreate(BaseModel):
    client_id: uuid.UUID
    brand: str
    model: str
    year: int = Field(ge=1900, le=2030)
    license_plate: str
    vin: str | None = None


class CarRead(BaseModel):
    id: uuid.UUID
    client_id: uuid.UUID
    brand: str
    model: str
    year: int
    license_plate: str
    vin: str | None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}


class CarUpdate(BaseModel):
    brand: str | None = None
    model: str | None = None
    year: int | None = None
    license_plate: str | None = None
    vin: str | None = None
