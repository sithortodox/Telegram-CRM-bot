import datetime
import uuid

from sqlalchemy import String, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class BlockedSlot(Base):
    __tablename__ = "blocked_slots"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    lift_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("lifts.id", ondelete="CASCADE"), index=True, nullable=True)
    staff_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("staff.id", ondelete="CASCADE"), index=True, nullable=True)
    date: Mapped[datetime.date] = mapped_column(index=True)
    start_time: Mapped[datetime.time] = mapped_column()
    end_time: Mapped[datetime.time] = mapped_column()
    reason: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    lift: Mapped["Lift | None"] = relationship(back_populates="blocked_slots")
    staff: Mapped["Staff | None"] = relationship(back_populates="blocked_slots")
