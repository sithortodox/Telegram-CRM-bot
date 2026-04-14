import uuid

from sqlalchemy import String, Integer, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import TimestampMixin, UUIDMixin


class Lift(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "lifts"

    name: Mapped[str] = mapped_column(String(100), unique=True)
    lift_type: Mapped[str] = mapped_column(String(50), default="standard")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="lift", cascade="all, delete-orphan")
    blocked_slots: Mapped[list["BlockedSlot"]] = relationship(back_populates="lift", cascade="all, delete-orphan")
