import uuid

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.database import async_session_factory
from src.services.booking import BookingService
from src.services.client_profile import ClientProfileService
from src.bot.common.keyboards import appointment_actions_keyboard, main_menu_keyboard
from src.bot.common.texts import MY_APPOINTMENTS_EMPTY, APPOINTMENT_CANCELLED

router = Router(name="client_cancellation")


class RescheduleStates(StatesGroup):
    selecting_date = State()
    selecting_time = State()


@router.message(F.text == "📋 Мои записи")
async def my_appointments(message: Message) -> None:
    async with async_session_factory() as session:
        client_service = ClientProfileService(session)
        client = await client_service.get_client_by_telegram_id(message.from_user.id)
        if not client:
            await message.answer("Вы ещё не зарегистрированы. Нажмите /start")
            return
        booking_service = BookingService(session)
        appointments = await booking_service.get_client_appointments(client.id, active_only=True)

    if not appointments:
        await message.answer(MY_APPOINTMENTS_EMPTY)
        return

    for apt in appointments:
        text = (
            f"📅 Дата: {apt.date.strftime('%d.%m.%Y')}\n"
            f"🕐 Время: {apt.start_time.strftime('%H:%M')} - {apt.end_time.strftime('%H:%M')}\n"
            f"📌 Статус: {apt.status}\n"
        )
        await message.answer(text, reply_markup=appointment_actions_keyboard(str(apt.id)))


@router.callback_query(F.data.startswith("cancel:"))
async def cancel_appointment(callback: CallbackQuery) -> None:
    appointment_id = callback.data.split(":", 1)[1]
    try:
        apt_uuid = uuid.UUID(appointment_id)
    except ValueError:
        await callback.message.answer("⚠️ Некорректный ID записи.")
        return

    async with async_session_factory() as session:
        booking_service = BookingService(session)
        try:
            await booking_service.cancel_by_client(apt_uuid)
            await session.commit()
        except ValueError as e:
            await callback.message.answer(f"⚠️ {e}")
            return

    await callback.message.answer(APPOINTMENT_CANCELLED, reply_markup=main_menu_keyboard())


@router.callback_query(F.data.startswith("reschedule:"))
async def reschedule_start(callback: CallbackQuery, state: FSMContext) -> None:
    appointment_id = callback.data.split(":", 1)[1]
    await state.update_data(appointment_id=appointment_id)

    import datetime
    today = datetime.date.today()
    dates = []
    for i in range(14):
        d = today + datetime.timedelta(days=i)
        if d.weekday() in [0, 1, 2, 3, 4, 5]:
            dates.append(d.strftime("%d.%m.%Y"))

    from src.bot.common.keyboards import dates_keyboard
    await callback.message.answer("📅 Выберите новую дату:", reply_markup=dates_keyboard(dates))
    await state.set_state(RescheduleStates.selecting_date)


@router.callback_query(RescheduleStates.selecting_date, F.data.startswith("date:"))
async def reschedule_select_time(callback: CallbackQuery, state: FSMContext) -> None:
    date_str = callback.data.split(":", 1)[1]
    await state.update_data(new_date=date_str)
    await callback.message.answer("🕐 Введите новое время в формате ЧЧ:ММ (например, 14:00):")
    await state.set_state(RescheduleStates.selecting_time)


@router.callback_query(RescheduleStates.selecting_time)
async def reschedule_confirm(callback: CallbackQuery, state: FSMContext) -> None:
    pass


@router.message(RescheduleStates.selecting_time)
async def reschedule_time_input(message: Message, state: FSMContext) -> None:
    import datetime

    try:
        new_time = datetime.datetime.strptime(message.text.strip(), "%H:%M").time()
    except ValueError:
        await message.answer("⚠️ Неверный формат. Используйте ЧЧ:ММ")
        return

    data = await state.get_data()
    appointment_id = data["appointment_id"]
    new_date = datetime.datetime.strptime(data["new_date"], "%d.%m.%Y").date()

    async with async_session_factory() as session:
        booking_service = BookingService(session)
        try:
            await booking_service.reschedule(uuid.UUID(appointment_id), new_date, new_time)
            await session.commit()
        except ValueError as e:
            await message.answer(f"⚠️ {e}")
            await state.clear()
            return

    await message.answer(
        f"✅ Запись перенесена на {data['new_date']} в {message.text.strip()}",
        reply_markup=main_menu_keyboard(),
    )
    await state.clear()
