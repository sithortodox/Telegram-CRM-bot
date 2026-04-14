import uuid

from sqlalchemy import String, Integer, Boolean, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import TimestampMixin, UUIDMixin


class Service(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "services"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    category: Mapped[str] = mapped_column(String(50))
    duration_minutes: Mapped[int] = mapped_column(Integer)
    requires_lift: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="service")
