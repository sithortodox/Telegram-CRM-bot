import datetime

from aiogram import Router, F
from aiogram.types import Message
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.database import async_session_factory
from src.services.booking import BookingService
from src.bot.common.keyboards import admin_main_keyboard
from src.bot.common.filters import AdminFilter

router = Router(name="admin_schedule")


@router.message(AdminFilter(), F.text == "📅 Расписание на сегодня")
async def today_schedule(message: Message) -> None:
    today = datetime.date.today()
    async with async_session_factory() as session:
        booking_service = BookingService(session)
        appointments = await booking_service.get_day_schedule(today)

    if not appointments:
        await message.answer("📅 На сегодня записей нет.")
        return

    text = f"📅 Расписание на {today.strftime('%d.%m.%Y')}:\n\n"
    for apt in appointments:
        from src.models.service import Service
        from src.models.client import Client
        service = await session.get(Service, apt.service_id)
        client = await session.get(Client, apt.client_id)

        text += (
            f"🕐 {apt.start_time.strftime('%H:%M')}-{apt.end_time.strftime('%H:%M')}\n"
            f"👤 {client.full_name} | 🔧 {service.name}\n"
            f"📌 Статус: {apt.status}\n\n"
        )

    await message.answer(text)


@router.message(AdminFilter(), F.text == "📅 Расписание на неделю")
async def week_schedule(message: Message) -> None:
    today = datetime.date.today()
    async with async_session_factory() as session:
        booking_service = BookingService(session)

        text = "📅 Расписание на неделю:\n\n"
        for i in range(7):
            d = today + datetime.timedelta(days=i)
            appointments = await booking_service.get_day_schedule(d)
            day_name = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"][d.weekday()]
            text += f"📌 {d.strftime('%d.%m')} ({day_name}): {len(appointments)} записей\n"

    await message.answer(text)
