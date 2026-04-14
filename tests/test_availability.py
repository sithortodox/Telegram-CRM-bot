import datetime

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.staff import Staff
from src.models.lift import Lift
from src.models.blocked_slot import BlockedSlot
from src.services.availability import AvailabilityService


async def _create_staff_and_lift(session: AsyncSession) -> dict:
    master = Staff(full_name="Мастер 1", role="master", is_active=True)
    session.add(master)
    await session.flush()

    lift = Lift(name="Подъемник 1", lift_type="standard", is_active=True)
    session.add(lift)
    await session.flush()

    return {"master": master, "lift": lift}


@pytest.mark.asyncio
async def test_available_masters(session: AsyncSession) -> None:
    data = await _create_staff_and_lift(session)
    availability_service = AvailabilityService(session)

    result = await availability_service.check_slot_availability(
        date=datetime.date.today(),
        start_time=datetime.time(10, 0),
        end_time=datetime.time(12, 0),
        requires_lift=False,
    )

    assert result["available"] is True
    assert data["master"].id in result["masters_available"]


@pytest.mark.asyncio
async def test_available_lifts(session: AsyncSession) -> None:
    data = await _create_staff_and_lift(session)
    availability_service = AvailabilityService(session)

    result = await availability_service.check_slot_availability(
        date=datetime.date.today(),
        start_time=datetime.time(10, 0),
        end_time=datetime.time(12, 0),
        requires_lift=True,
    )

    assert result["available"] is True
    assert data["lift"].id in result["lifts_available"]


@pytest.mark.asyncio
async def test_blocked_lift_unavailable(session: AsyncSession) -> None:
    data = await _create_staff_and_lift(session)

    blocked = BlockedSlot(
        lift_id=data["lift"].id,
        date=datetime.date.today(),
        start_time=datetime.time(9, 0),
        end_time=datetime.time(21, 0),
        reason="Ремонт подъемника",
    )
    session.add(blocked)
    await session.flush()

    availability_service = AvailabilityService(session)
    result = await availability_service.check_slot_availability(
        date=datetime.date.today(),
        start_time=datetime.time(10, 0),
        end_time=datetime.time(12, 0),
        requires_lift=True,
    )

    assert result["available"] is False
