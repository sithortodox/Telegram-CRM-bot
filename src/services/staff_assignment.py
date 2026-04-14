import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.staff import Staff
from src.schemas.staff import StaffCreate, StaffUpdate


class StaffAssignmentService:
    """Сервис управления мастерами"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_staff(self, data: StaffCreate) -> Staff:
        staff = Staff(
            telegram_id=data.telegram_id,
            full_name=data.full_name,
            role=data.role.value,
            phone=data.phone,
            specializations=data.specializations,
            is_active=True,
        )
        self.session.add(staff)
        await self.session.flush()
        return staff

    async def update_staff(self, staff_id: uuid.UUID, data: StaffUpdate) -> Staff:
        staff = await self._get_staff(staff_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(staff, field, value)
        await self.session.flush()
        return staff

    async def deactivate_staff(self, staff_id: uuid.UUID) -> Staff:
        staff = await self._get_staff(staff_id)
        staff.is_active = False
        await self.session.flush()
        return staff

    async def activate_staff(self, staff_id: uuid.UUID) -> Staff:
        staff = await self._get_staff(staff_id)
        staff.is_active = True
        await self.session.flush()
        return staff

    async def get_all_masters(self, active_only: bool = True) -> list[Staff]:
        query = select(Staff).where(Staff.role == "master")
        if active_only:
            query = query.where(Staff.is_active.is_(True))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_staff_by_telegram_id(self, telegram_id: int) -> Staff | None:
        query = select(Staff).where(Staff.telegram_id == telegram_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def _get_staff(self, staff_id: uuid.UUID) -> Staff:
        staff = await self.session.get(Staff, staff_id)
        if not staff:
            raise ValueError("Сотрудник не найден")
        return staff
