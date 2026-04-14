import asyncio
import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.config import settings
from src.utils.logging import get_logger

logger = get_logger("scheduler")

scheduler = AsyncIOScheduler()


async def send_day_reminders() -> None:
    """Напоминания за день до визита"""
    from src.database import async_session_factory
    from src.services.reminder import ReminderService
    from src.bot.common.texts import APPOINTMENT_REMINDER_DAY

    async with async_session_factory() as session:
        reminder_service = ReminderService(session)
        appointments = await reminder_service.get_appointments_for_day_reminder()

        for apt in appointments:
            try:
                from src.models.client import Client
                from src.models.service import Service
                client = await session.get(Client, apt.client_id)
                service = await session.get(Service, apt.service_id)

                if client and service:
                    logger.info("day_reminder", telegram_id=client.telegram_id, appointment_id=str(apt.id))
                    await reminder_service.mark_day_reminder_sent(apt.id)

            except Exception as e:
                logger.error("day_reminder_error", appointment_id=str(apt.id), error=str(e))

        await session.commit()


async def send_2h_reminders() -> None:
    """Напоминания за 2 часа до визита"""
    from src.database import async_session_factory
    from src.services.reminder import ReminderService
    from src.bot.common.texts import APPOINTMENT_REMINDER_2H

    async with async_session_factory() as session:
        reminder_service = ReminderService(session)
        appointments = await reminder_service.get_appointments_for_2h_reminder()

        for apt in appointments:
            try:
                from src.models.client import Client
                from src.models.service import Service
                client = await session.get(Client, apt.client_id)
                service = await session.get(Service, apt.service_id)

                if client and service:
                    logger.info("2h_reminder", telegram_id=client.telegram_id, appointment_id=str(apt.id))
                    await reminder_service.mark_2h_reminder_sent(apt.id)

            except Exception as e:
                logger.error("2h_reminder_error", appointment_id=str(apt.id), error=str(e))

        await session.commit()


async def request_feedbacks() -> None:
    """Запрос отзывов после завершённых визитов"""
    from src.database import async_session_factory
    from src.services.reminder import ReminderService

    async with async_session_factory() as session:
        reminder_service = ReminderService(session)
        appointments = await reminder_service.get_completed_without_feedback()

        for apt in appointments:
            try:
                from src.models.client import Client
                client = await session.get(Client, apt.client_id)
                if client:
                    logger.info("feedback_request", telegram_id=client.telegram_id, appointment_id=str(apt.id))
            except Exception as e:
                logger.error("feedback_request_error", appointment_id=str(apt.id), error=str(e))


def setup_scheduler() -> None:
    """Настройка периодических задач"""
    scheduler.add_job(send_day_reminders, "cron", hour=18, minute=0, id="day_reminders")
    scheduler.add_job(send_2h_reminders, "cron", minute="*/15", id="2h_reminders")
    scheduler.add_job(request_feedbacks, "cron", hour=20, minute=0, id="feedback_requests")

    logger.info("scheduler_configured", jobs=[j.id for j in scheduler.get_jobs()])
