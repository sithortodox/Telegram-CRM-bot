import datetime
import uuid

from sqlalchemy import String, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class AppointmentStatusHistory(Base):
    __tablename__ = "appointment_status_history"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    appointment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("appointments.id", ondelete="CASCADE"), index=True)
    old_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    new_status: Mapped[str] = mapped_column(String(30))
    changed_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    changed_by: Mapped[str] = mapped_column(String(50))
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    appointment: Mapped["Appointment"] = relationship(back_populates="status_history")
