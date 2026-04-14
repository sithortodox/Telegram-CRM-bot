import datetime
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.blocked_slot import BlockedSlot
from src.models.lift import Lift


class LiftAllocationService:
    """Сервис управления подъемниками"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all_lifts(self, active_only: bool = True) -> list[Lift]:
        query = select(Lift)
        if active_only:
            query = query.where(Lift.is_active.is_(True))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def block_lift(
        self,
        lift_id: uuid.UUID,
        date: datetime.date,
        start_time: datetime.time,
        end_time: datetime.time,
        reason: str,
        staff_id: uuid.UUID | None = None,
    ) -> BlockedSlot:
        """Блокировка подъемника на указанный интервал"""
        blocked = BlockedSlot(
            lift_id=lift_id,
            staff_id=staff_id,
            date=date,
            start_time=start_time,
            end_time=end_time,
            reason=reason,
        )
        self.session.add(blocked)
        await self.session.flush()
        return blocked

    async def unblock_slot(self, slot_id: uuid.UUID) -> bool:
        """Разблокировка слота"""
        slot = await self.session.get(BlockedSlot, slot_id)
        if not slot:
            raise ValueError("Заблокированный слот не найден")
        await self.session.delete(slot)
        await self.session.flush()
        return True

    async def deactivate_lift(self, lift_id: uuid.UUID) -> Lift:
        lift = await self._get_lift(lift_id)
        lift.is_active = False
        await self.session.flush()
        return lift

    async def activate_lift(self, lift_id: uuid.UUID) -> Lift:
        lift = await self._get_lift(lift_id)
        lift.is_active = True
        await self.session.flush()
        return lift

    async def _get_lift(self, lift_id: uuid.UUID) -> Lift:
        lift = await self.session.get(Lift, lift_id)
        if not lift:
            raise ValueError("Подъемник не найден")
        return lift
