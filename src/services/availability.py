import datetime
import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import AppointmentStatusEnum, settings
from src.models.appointment import Appointment
from src.models.blocked_slot import BlockedSlot
from src.models.lift import Lift
from src.models.staff import Staff


class AvailabilityService:
    """Сервис проверки доступности слотов"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def check_slot_availability(
        self,
        date: datetime.date,
        start_time: datetime.time,
        end_time: datetime.time,
        requires_lift: bool = False,
        master_id: uuid.UUID | None = None,
        lift_id: uuid.UUID | None = None,
        exclude_appointment_id: uuid.UUID | None = None,
    ) -> dict:
        """Проверка доступности слота с учетом всех ограничений"""
        if not self._is_working_day(date):
            return {"available": False, "reason": "Нерабочий день", "masters_available": [], "lifts_available": []}

        if not self._is_within_working_hours(start_time, end_time):
            return {"available": False, "reason": "Вне рабочих часов", "masters_available": [], "lifts_available": []}

        blocked_slots = await self._get_blocked_slots(date, start_time, end_time)

        available_masters = await self._get_available_masters(
            date, start_time, end_time, blocked_slots, exclude_appointment_id
        )

        available_lifts = []
        if requires_lift:
            available_lifts = await self._get_available_lifts(
                date, start_time, end_time, blocked_slots, exclude_appointment_id
            )
            if not available_lifts:
                return {"available": False, "reason": "Нет свободных подъемников", "masters_available": available_masters, "lifts_available": []}

        if master_id:
            master_ids = [m.id for m in available_masters]
            if master_id not in master_ids:
                return {"available": False, "reason": "Мастер недоступен", "masters_available": available_masters, "lifts_available": available_lifts}

        if lift_id and requires_lift:
            lift_ids = [l.id for l in available_lifts]
            if lift_id not in lift_ids:
                return {"available": False, "reason": "Подъемник недоступен", "masters_available": available_masters, "lifts_available": available_lifts}

        return {
            "available": True,
            "reason": None,
            "masters_available": [m.id for m in available_masters],
            "lifts_available": [l.id for l in available_lifts],
        }

    async def get_available_slots(
        self,
        date: datetime.date,
        service_duration_minutes: int,
        requires_lift: bool = False,
    ) -> list[dict]:
        """Получение списка доступных слотов на указанную дату"""
        if not self._is_working_day(date):
            return []

        slots: list[dict] = []
        work_start = settings.work_start_time
        work_end = settings.work_end_time
        slot_interval = datetime.timedelta(minutes=30)

        current_dt = datetime.datetime.combine(datetime.date.min, work_start)
        end_dt = datetime.datetime.combine(datetime.date.min, work_end)

        while current_dt + datetime.timedelta(minutes=service_duration_minutes) <= end_dt:
            slot_start = current_dt.time()
            slot_end = (
                current_dt + datetime.timedelta(minutes=service_duration_minutes)
            ).time()

            availability = await self.check_slot_availability(
                date=date,
                start_time=slot_start,
                end_time=slot_end,
                requires_lift=requires_lift,
            )

            slots.append({
                "start_time": slot_start,
                "end_time": slot_end,
                "available": availability["available"],
                "masters_available": availability["masters_available"],
                "lifts_available": availability["lifts_available"],
            })

            current_dt += slot_interval

        return slots

    async def _get_available_masters(
        self,
        date: datetime.date,
        start_time: datetime.time,
        end_time: datetime.time,
        blocked_slots: list[BlockedSlot],
        exclude_appointment_id: uuid.UUID | None = None,
    ) -> list[Staff]:
        """Получение списка доступных мастеров"""
        query = select(Staff).where(Staff.is_active.is_(True), Staff.role == "master")
        result = await self.session.execute(query)
        all_masters = list(result.scalars().all())

        blocked_staff_ids = {
            bs.staff_id for bs in blocked_slots if bs.staff_id
        }

        conflicting_appointments = await self._get_conflicting_appointments(
            date, start_time, end_time, exclude_appointment_id
        )
        busy_master_ids = {a.master_id for a in conflicting_appointments if a.master_id}

        available = []
        for master in all_masters:
            if master.id in blocked_staff_ids:
                continue
            if master.id in busy_master_ids:
                continue
            available.append(master)

        return available

    async def _get_available_lifts(
        self,
        date: datetime.date,
        start_time: datetime.time,
        end_time: datetime.time,
        blocked_slots: list[BlockedSlot],
        exclude_appointment_id: uuid.UUID | None = None,
    ) -> list[Lift]:
        """Получение списка доступных подъемников"""
        query = select(Lift).where(Lift.is_active.is_(True))
        result = await self.session.execute(query)
        all_lifts = list(result.scalars().all())

        blocked_lift_ids = {
            bs.lift_id for bs in blocked_slots if bs.lift_id
        }

        conflicting_appointments = await self._get_conflicting_appointments(
            date, start_time, end_time, exclude_appointment_id
        )
        busy_lift_ids = {a.lift_id for a in conflicting_appointments if a.lift_id}

        available = []
        for lift in all_lifts:
            if lift.id in blocked_lift_ids:
                continue
            if lift.id in busy_lift_ids:
                continue
            available.append(lift)

        return available

    async def _get_conflicting_appointments(
        self,
        date: datetime.date,
        start_time: datetime.time,
        end_time: datetime.time,
        exclude_appointment_id: uuid.UUID | None = None,
    ) -> list[Appointment]:
        """Получение конфликтующих записей"""
        active_statuses = [
            AppointmentStatusEnum.CREATED.value,
            AppointmentStatusEnum.CONFIRMED.value,
            AppointmentStatusEnum.REMINDER_SENT_DAY_BEFORE.value,
            AppointmentStatusEnum.REMINDER_SENT_2H_BEFORE.value,
            AppointmentStatusEnum.IN_PROGRESS.value,
        ]

        query = select(Appointment).where(
            Appointment.date == date,
            Appointment.status.in_(active_statuses),
            Appointment.start_time < end_time,
            Appointment.end_time > start_time,
        )

        if exclude_appointment_id:
            query = query.where(Appointment.id != exclude_appointment_id)

        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _get_blocked_slots(
        self,
        date: datetime.date,
        start_time: datetime.time,
        end_time: datetime.time,
    ) -> list[BlockedSlot]:
        """Получение заблокированных слотов"""
        query = select(BlockedSlot).where(
            BlockedSlot.date == date,
            BlockedSlot.start_time < end_time,
            BlockedSlot.end_time > start_time,
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    def _is_working_day(self, date: datetime.date) -> bool:
        return date.weekday() in settings.work_days_list

    def _is_within_working_hours(self, start: datetime.time, end: datetime.time) -> bool:
        return start >= settings.work_start_time and end <= settings.work_end_time
