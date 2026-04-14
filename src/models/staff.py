import uuid

from sqlalchemy import String, BigInteger, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config import RoleEnum
from src.database import Base
from src.models.base import TimestampMixin, UUIDMixin


class Staff(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "staff"

    telegram_id: Mapped[int | None] = mapped_column(BigInteger, unique=True, nullable=True)
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default=RoleEnum.MASTER.value)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    specializations: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    appointments: Mapped[list["Appointment"]] = relationship(back_populates="master", cascade="all, delete-orphan")
    blocked_slots: Mapped[list["BlockedSlot"]] = relationship(back_populates="staff", cascade="all, delete-orphan")
