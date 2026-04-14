import datetime

from aiogram import Router, F
from aiogram.types import Message

from src.database import async_session_factory
from src.services.feedback import FeedbackService
from src.services.booking import BookingService
from src.bot.common.filters import AdminFilter

router = Router(name="admin_analytics")


@router.message(AdminFilter(), F.text == "📊 Аналитика")
async def analytics_menu(message: Message) -> None:
    async with async_session_factory() as session:
        booking_service = BookingService(session)
        feedback_service = FeedbackService(session)

        today = datetime.date.today()
        week_ago = today - datetime.timedelta(days=7)

        from sqlalchemy import select, func, and_
        from src.models.appointment import Appointment
        from src.models.feedback import Feedback
        from src.models.client import Client

        total_clients = await session.scalar(select(func.count(Client.id)))
        total_appointments = await session.scalar(
            select(func.count(Appointment.id)).where(Appointment.date >= week_ago)
        )
        cancelled = await session.scalar(
            select(func.count(Appointment.id)).where(
                Appointment.date >= week_ago,
                Appointment.status.in_(["cancelled_by_client", "cancelled_by_admin"]),
            )
        )
        no_show = await session.scalar(
            select(func.count(Appointment.id)).where(
                Appointment.date >= week_ago,
                Appointment.status == "no_show",
            )
        )
        avg_rating = await feedback_service.get_average_rating()

        repeat_clients = await session.scalar(
            select(func.count(func.distinct(Appointment.client_id))).where(
                Appointment.date >= week_ago,
            )
        )

    text = (
        f"📊 Аналитика за неделю:\n\n"
        f"👥 Всего клиентов: {total_clients}\n"
        f"📋 Записей за неделю: {total_appointments}\n"
        f"❌ Отмен: {cancelled}\n"
        f"🚫 Не явились: {no_show}\n"
        f"⭐ Средняя оценка: {avg_rating:.1f}\n"
    )

    await message.answer(text)
