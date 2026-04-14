import datetime
import uuid

from pydantic import BaseModel, Field


class FeedbackCreate(BaseModel):
    appointment_id: uuid.UUID
    client_id: uuid.UUID
    rating: int = Field(ge=1, le=5)
    comment: str | None = None


class FeedbackRead(BaseModel):
    id: uuid.UUID
    appointment_id: uuid.UUID
    client_id: uuid.UUID
    rating: int
    comment: str | None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
