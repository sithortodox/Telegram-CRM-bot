import datetime
import uuid

from sqlalchemy import BigInteger, String, Boolean, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import TimestampMixin, UUIDMixin


class Client(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "clients"

    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    username: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str] = mapped_column(String(20), index=True)
    data_consent: Mapped[bool] = mapped_column(Boolean, default=False)
    data_consent_at: Mapped[datetime.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    cars: Mapped[list["Car"]] = relationship(back_populates="client", cascade="all, delete-orphan")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="client", cascade="all, delete-orphan")
    feedbacks: Mapped[list["Feedback"]] = relationship(back_populates="client", cascade="all, delete-orphan")
