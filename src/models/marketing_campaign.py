import datetime
import uuid

from sqlalchemy import String, Integer, DateTime, Text, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class MarketingCampaign(Base):
    __tablename__ = "marketing_campaigns"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255))
    message_text: Mapped[str] = mapped_column(Text)
    target_filter: Mapped[str | None] = mapped_column(String(500), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft")
    total_recipients: Mapped[int] = mapped_column(Integer, default=0)
    sent_count: Mapped[int] = mapped_column(Integer, default=0)
    failed_count: Mapped[int] = mapped_column(Integer, default=0)
    scheduled_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    started_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
