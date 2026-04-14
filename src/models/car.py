import uuid

from sqlalchemy import String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.database import Base
from src.models.base import TimestampMixin, UUIDMixin


class Car(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "cars"

    client_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("clients.id", ondelete="CASCADE"), index=True)
    brand: Mapped[str] = mapped_column(String(100))
    model: Mapped[str] = mapped_column(String(100))
    year: Mapped[int] = mapped_column(Integer)
    license_plate: Mapped[str] = mapped_column(String(20), index=True)
    vin: Mapped[str | None] = mapped_column(String(17), nullable=True, unique=True)

    client: Mapped["Client"] = relationship(back_populates="cars")
    appointments: Mapped[list["Appointment"]] = relationship(back_populates="car", cascade="all, delete-orphan")

    __table_args__ = (UniqueConstraint("client_id", "license_plate", name="uq_car_client_license"),)
