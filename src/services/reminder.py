import datetime
import logging
import uuid

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.config import AppointmentStatusEnum
from src.models.appointment import Appointment

logger = logging.getLogger(__name__)


class ReminderService:
    """Сервис напоминаний клиентам"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_appointments_for_day_reminder(self) -> list[Appointment]:
        """Записи для напоминания за день"""
        tomorrow = datetime.date.today() + datetime.timedelta(days=1)
        target_statuses = [
            AppointmentStatusEnum.CONFIRMED.value,
        ]
        query = select(Appointment).where(
            Appointment.date == tomorrow,
            Appointment.status.in_(target_statuses),
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_appointments_for_2h_reminder(self) -> list[Appointment]:
        """Записи для напоминания за 2 часа"""
        now = datetime.datetime.now()
        target_date = now.date()
        target_time_from = (now + datetime.timedelta(hours=2)).time()
        target_time_to = (now + datetime.timedelta(hours=2, minutes=30)).time()

        target_statuses = [
            AppointmentStatusEnum.CONFIRMED.value,
            AppointmentStatusEnum.REMINDER_SENT_DAY_BEFORE.value,
        ]
        query = select(Appointment).where(
            Appointment.date == target_date,
            Appointment.start_time >= target_time_from,
            Appointment.start_time < target_time_to,
            Appointment.status.in_(target_statuses),
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def mark_day_reminder_sent(self, appointment_id: uuid.UUID) -> None:
        """Отметка об отправке напоминания за день"""
        appointment = await self.session.get(Appointment, appointment_id)
        if appointment:
            old_status = appointment.status
            appointment.status = AppointmentStatusEnum.REMINDER_SENT_DAY_BEFORE.value
            from src.models.appointment_status_history import AppointmentStatusHistory
            self.session.add(AppointmentStatusHistory(
                appointment_id=appointment_id,
                old_status=old_status,
                new_status=AppointmentStatusEnum.REMINDER_SENT_DAY_BEFORE.value,
                changed_by="system_reminder",
            ))
            await self.session.flush()

    async def mark_2h_reminder_sent(self, appointment_id: uuid.UUID) -> None:
        """Отметка об отправке напоминания за 2 часа"""
        appointment = await self.session.get(Appointment, appointment_id)
        if appointment:
            old_status = appointment.status
            appointment.status = AppointmentStatusEnum.REMINDER_SENT_2H_BEFORE.value
            from src.models.appointment_status_history import AppointmentStatusHistory
            self.session.add(AppointmentStatusHistory(
                appointment_id=appointment_id,
                old_status=old_status,
                new_status=AppointmentStatusEnum.REMINDER_SENT_2H_BEFORE.value,
                changed_by="system_reminder",
            ))
            await self.session.flush()

    async def get_completed_without_feedback(self) -> list[Appointment]:
        """Завершённые визиты без отзыва (за последние 24 часа)"""
        from src.models.feedback import Feedback

        cutoff = datetime.datetime.now() - datetime.timedelta(hours=24)
        feedback_query = select(Feedback.appointment_id)
        feedback_result = await self.session.execute(feedback_query)
        feedback_ids = set(feedback_result.scalars().all())

        query = select(Appointment).where(
            Appointment.status == AppointmentStatusEnum.COMPLETED.value,
            Appointment.updated_at >= cutoff,
        )
        result = await self.session.execute(query)
        appointments = list(result.scalars().all())

        return [a for a in appointments if a.id not in feedback_ids]
