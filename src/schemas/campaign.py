import datetime
import uuid

from pydantic import BaseModel


class CampaignCreate(BaseModel):
    name: str
    message_text: str
    target_filter: str | None = None
    scheduled_at: datetime.datetime | None = None


class CampaignRead(BaseModel):
    id: uuid.UUID
    name: str
    message_text: str
    target_filter: str | None
    status: str
    total_recipients: int
    sent_count: int
    failed_count: int
    scheduled_at: datetime.datetime | None
    started_at: datetime.datetime | None
    completed_at: datetime.datetime | None
    created_at: datetime.datetime

    model_config = {"from_attributes": True}
