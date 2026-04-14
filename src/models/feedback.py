import datetime
import uuid

from sqlalchemy import String, Integer, ForeignKey, DateTime, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base


class Feedback(Base):
    __tablename__ = "feedbacks"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    appointment_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("appointments.id", ondelete="CASCADE"), unique=True, index=True)
    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    appointment: Mapped["Appointment"] = relationship(back_populates="feedback")
    client: Mapped["Client"] = relationship(back_populates="feedbacks")
