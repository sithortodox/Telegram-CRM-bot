import datetime
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.client import Client
from src.models.car import Car
from src.models.service import Service
from src.models.staff import Staff
from src.models.lift import Lift
from src.models.appointment import Appointment
from src.config import AppointmentStatusEnum
from src.services.booking import BookingService
from src.services.availability import AvailabilityService
from src.schemas.appointment import AppointmentCreate


async def _create_test_data(session: AsyncSession) -> dict:
    """Создание тестовых данных"""
    client = Client(
        telegram_id=123456,
        username="testuser",
        full_name="Тестовый Клиент",
        phone="+79001234567",
        data_consent=True,
    )
    session.add(client)
    await session.flush()

    car = Car(
        client_id=client.id,
        brand="Toyota",
        model="Camry",
        year=2020,
        license_plate="А123АА77",
    )
    session.add(car)
    await session.flush()

    service = Service(
        name="ТО",
        category="ТО",
        duration_minutes=120,
        requires_lift=True,
    )
    session.add(service)
    await session.flush()

    master = Staff(
        full_name="Тестовый Мастер",
        role="master",
        is_active=True,
    )
    session.add(master)
    await session.flush()

    lift = Lift(
        name="Подъемник 1",
        lift_type="standard",
        is_active=True,
    )
    session.add(lift)
    await session.flush()

    return {
        "client": client,
        "car": car,
        "service": service,
        "master": master,
        "lift": lift,
    }


@pytest.mark.asyncio
async def test_create_appointment(session: AsyncSession) -> None:
    data = await _create_test_data(session)

    booking_service = BookingService(session)
    appointment_data = AppointmentCreate(
        client_id=data["client"].id,
        car_id=data["car"].id,
        service_id=data["service"].id,
        master_id=data["master"].id,
        lift_id=data["lift"].id,
        date=datetime.date.today(),
        start_time=datetime.time(10, 0),
    )

    appointment = await booking_service.create_appointment(appointment_data)
    assert appointment.status == AppointmentStatusEnum.CREATED.value
    assert appointment.start_time == datetime.time(10, 0)
    assert appointment.end_time == datetime.time(12, 0)


@pytest.mark.asyncio
async def test_cancel_appointment(session: AsyncSession) -> None:
    data = await _create_test_data(session)
    booking_service = BookingService(session)

    appointment_data = AppointmentCreate(
        client_id=data["client"].id,
        car_id=data["car"].id,
        service_id=data["service"].id,
        master_id=data["master"].id,
        lift_id=data["lift"].id,
        date=datetime.date.today(),
        start_time=datetime.time(10, 0),
    )

    appointment = await booking_service.create_appointment(appointment_data)
    await session.flush()

    cancelled = await booking_service.cancel_by_client(appointment.id)
    assert cancelled.status == AppointmentStatusEnum.CANCELLED_BY_CLIENT.value


@pytest.mark.asyncio
async def test_availability_check(session: AsyncSession) -> None:
    data = await _create_test_data(session)
    availability_service = AvailabilityService(session)

    result = await availability_service.check_slot_availability(
        date=datetime.date.today(),
        start_time=datetime.time(10, 0),
        end_time=datetime.time(12, 0),
        requires_lift=True,
        master_id=data["master"].id,
        lift_id=data["lift"].id,
    )

    assert result["available"] is True


@pytest.mark.asyncio
async def test_double_booking_prevention(session: AsyncSession) -> None:
    data = await _create_test_data(session)
    booking_service = BookingService(session)

    appointment_data = AppointmentCreate(
        client_id=data["client"].id,
        car_id=data["car"].id,
        service_id=data["service"].id,
        master_id=data["master"].id,
        lift_id=data["lift"].id,
        date=datetime.date.today(),
        start_time=datetime.time(10, 0),
    )

    await booking_service.create_appointment(appointment_data)
    await session.flush()

    with pytest.raises(ValueError, match="недоступен"):
        await booking_service.create_appointment(appointment_data)
