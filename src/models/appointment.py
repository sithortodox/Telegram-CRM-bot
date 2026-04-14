import datetime
import uuid

from sqlalchemy import String, Integer, ForeignKey, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config import AppointmentStatusEnum
from src.database import Base
from src.models.base import TimestampMixin, UUIDMixin


class Appointment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "appointments"

    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    car_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("cars.id", ondelete="CASCADE"), index=True)
    service_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("services.id", ondelete="RESTRICT"), index=True)
    master_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("staff.id", ondelete="SET NULL"), index=True, nullable=True)
    lift_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("lifts.id", ondelete="SET NULL"), index=True, nullable=True)

    date: Mapped[datetime.date] = mapped_column(index=True)
    start_time: Mapped[datetime.time] = mapped_column()
    end_time: Mapped[datetime.time] = mapped_column()
    status: Mapped[str] = mapped_column(String(30), default=AppointmentStatusEnum.CREATED.value, index=True)
    client_comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    client: Mapped["Client"] = relationship(back_populates="appointments")
    car: Mapped["Car"] = relationship(back_populates="appointments")
    service: Mapped["Service"] = relationship(back_populates="appointments")
    master: Mapped["Staff | None"] = relationship(back_populates="appointments")
    lift: Mapped["Lift | None"] = relationship(back_populates="appointments")
    status_history: Mapped[list["AppointmentStatusHistory"]] = relationship(back_populates="appointment", cascade="all, delete-orphan")
    feedback: Mapped["Feedback | None"] = relationship(back_populates="appointment", uselist=False, cascade="all, delete-orphan")
