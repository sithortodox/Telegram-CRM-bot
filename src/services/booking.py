import datetime
import uuid

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import AppointmentStatusEnum, settings
from src.models.appointment import Appointment
from src.models.appointment_status_history import AppointmentStatusHistory
from src.models.car import Car
from src.models.client import Client
from src.models.lift import Lift
from src.models.service import Service
from src.models.staff import Staff
from src.schemas.appointment import AppointmentCreate, AppointmentUpdate
from src.services.availability import AvailabilityService


class BookingService:
    """Сервис записи клиентов"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
        self.availability = AvailabilityService(session)

    async def create_appointment(self, data: AppointmentCreate) -> Appointment:
        """Создание записи с проверкой доступности слота"""
        service = await self.session.get(Service, data.service_id)
        if not service:
            raise ValueError("Услуга не найдена")

        end_time = (
            datetime.datetime.combine(datetime.date.min, data.start_time)
            + datetime.timedelta(minutes=service.duration_minutes)
        ).time()

        availability = await self.availability.check_slot_availability(
            date=data.date,
            start_time=data.start_time,
            end_time=end_time,
            requires_lift=service.requires_lift,
            master_id=data.master_id,
            lift_id=data.lift_id,
        )

        if not availability["available"]:
            raise ValueError(f"Слот недоступен: {availability['reason']}")

        master_id = data.master_id
        lift_id = data.lift_id

        if not master_id and availability["masters_available"]:
            master_id = availability["masters_available"][0]
        if not lift_id and service.requires_lift and availability["lifts_available"]:
            lift_id = availability["lifts_available"][0]

        if service.requires_lift and not lift_id:
            raise ValueError("Нет свободных подъемников для данной услуги")

        appointment = Appointment(
            client_id=data.client_id,
            car_id=data.car_id,
            service_id=data.service_id,
            master_id=master_id,
            lift_id=lift_id,
            date=data.date,
            start_time=data.start_time,
            end_time=end_time,
            status=AppointmentStatusEnum.CREATED.value,
            client_comment=data.client_comment,
        )
        self.session.add(appointment)
        await self.session.flush()

        await self._add_status_history(
            appointment_id=appointment.id,
            old_status=None,
            new_status=AppointmentStatusEnum.CREATED.value,
            changed_by="client",
        )

        await self.session.flush()
        return appointment

    async def confirm_appointment(self, appointment_id: uuid.UUID) -> Appointment:
        """Подтверждение записи"""
        appointment = await self._get_appointment(appointment_id)
        return await self._change_status(
            appointment, AppointmentStatusEnum.CONFIRMED.value, "system"
        )

    async def cancel_by_client(self, appointment_id: uuid.UUID) -> Appointment:
        """Отмена записи клиентом"""
        appointment = await self._get_appointment(appointment_id)
        return await self._change_status(
            appointment, AppointmentStatusEnum.CANCELLED_BY_CLIENT.value, "client"
        )

    async def cancel_by_admin(self, appointment_id: uuid.UUID, admin_name: str) -> Appointment:
        """Отмена записи администратором"""
        appointment = await self._get_appointment(appointment_id)
        return await self._change_status(
            appointment, AppointmentStatusEnum.CANCELLED_BY_ADMIN.value, admin_name
        )

    async def reschedule(
        self,
        appointment_id: uuid.UUID,
        new_date: datetime.date,
        new_start_time: datetime.time,
    ) -> Appointment:
        """Перенос записи"""
        appointment = await self._get_appointment(appointment_id)
        service = await self.session.get(Service, appointment.service_id)

        new_end_time = (
            datetime.datetime.combine(datetime.date.min, new_start_time)
            + datetime.timedelta(minutes=service.duration_minutes)
        ).time()

        availability = await self.availability.check_slot_availability(
            date=new_date,
            start_time=new_start_time,
            end_time=new_end_time,
            requires_lift=service.requires_lift,
            master_id=appointment.master_id,
            lift_id=appointment.lift_id,
            exclude_appointment_id=appointment_id,
        )

        if not availability["available"]:
            raise ValueError(f"Новый слот недоступен: {availability['reason']}")

        old_status = appointment.status
        appointment.date = new_date
        appointment.start_time = new_start_time
        appointment.end_time = new_end_time
        appointment.status = AppointmentStatusEnum.RESCHEDULED.value

        await self._add_status_history(
            appointment_id=appointment.id,
            old_status=old_status,
            new_status=AppointmentStatusEnum.RESCHEDULED.value,
            changed_by="client",
        )
        await self.session.flush()
        return appointment

    async def start_appointment(self, appointment_id: uuid.UUID) -> Appointment:
        """Начало выполнения работ"""
        appointment = await self._get_appointment(appointment_id)
        return await self._change_status(
            appointment, AppointmentStatusEnum.IN_PROGRESS.value, "system"
        )

    async def complete_appointment(self, appointment_id: uuid.UUID) -> Appointment:
        """Завершение визита"""
        appointment = await self._get_appointment(appointment_id)
        return await self._change_status(
            appointment, AppointmentStatusEnum.COMPLETED.value, "system"
        )

    async def mark_no_show(self, appointment_id: uuid.UUID, admin_name: str) -> Appointment:
        """Отметка «не явился»"""
        appointment = await self._get_appointment(appointment_id)
        return await self._change_status(
            appointment, AppointmentStatusEnum.NO_SHOW.value, admin_name
        )

    async def update_appointment(
        self, appointment_id: uuid.UUID, data: AppointmentUpdate
    ) -> Appointment:
        """Обновление записи администратором"""
        appointment = await self._get_appointment(appointment_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(appointment, field, value)
        await self.session.flush()
        return appointment

    async def get_client_appointments(
        self, client_id: uuid.UUID, active_only: bool = False
    ) -> list[Appointment]:
        """Получение записей клиента"""
        query = select(Appointment).where(Appointment.client_id == client_id)
        if active_only:
            active_statuses = [
                AppointmentStatusEnum.CREATED.value,
                AppointmentStatusEnum.CONFIRMED.value,
                AppointmentStatusEnum.REMINDER_SENT_DAY_BEFORE.value,
                AppointmentStatusEnum.REMINDER_SENT_2H_BEFORE.value,
                AppointmentStatusEnum.IN_PROGRESS.value,
            ]
            query = query.where(Appointment.status.in_(active_statuses))
        query = query.order_by(Appointment.date, Appointment.start_time)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_day_schedule(self, date: datetime.date) -> list[Appointment]:
        """Расписание на день"""
        query = (
            select(Appointment)
            .where(Appointment.date == date)
            .order_by(Appointment.start_time)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _get_appointment(self, appointment_id: uuid.UUID) -> Appointment:
        appointment = await self.session.get(Appointment, appointment_id)
        if not appointment:
            raise ValueError("Запись не найдена")
        return appointment

    async def _change_status(
        self, appointment: Appointment, new_status: str, changed_by: str
    ) -> Appointment:
        old_status = appointment.status
        appointment.status = new_status
        await self._add_status_history(
            appointment_id=appointment.id,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
        )
        await self.session.flush()
        return appointment

    async def _add_status_history(
        self,
        appointment_id: uuid.UUID,
        old_status: str | None,
        new_status: str,
        changed_by: str,
        comment: str | None = None,
    ) -> None:
        history = AppointmentStatusHistory(
            appointment_id=appointment_id,
            old_status=old_status,
            new_status=new_status,
            changed_by=changed_by,
            comment=comment,
        )
        self.session.add(history)
