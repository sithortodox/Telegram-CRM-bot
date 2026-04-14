import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.database import async_session_factory
from src.services.client_profile import ClientProfileService
from src.services.availability import AvailabilityService
from src.services.booking import BookingService
from src.models.service import Service
from src.bot.common.keyboards import (
    service_categories_keyboard,
    services_keyboard,
    dates_keyboard,
    time_slots_keyboard,
    cars_keyboard,
    confirm_keyboard,
    main_menu_keyboard,
)
from src.bot.common.texts import (
    SERVICE_SELECTION,
    DATE_SELECTION,
    TIME_SELECTION,
    NO_SLOTS_AVAILABLE,
    APPOINTMENT_CONFIRMED,
)

router = Router(name="client_booking")


class BookingStates(StatesGroup):
    selecting_category = State()
    selecting_service = State()
    selecting_car = State()
    selecting_date = State()
    selecting_time = State()
    confirming = State()


@router.message(F.text == "📝 Записаться")
async def start_booking(message: Message, state: FSMContext) -> None:
    async with async_session_factory() as session:
        client_service = ClientProfileService(session)
        client = await client_service.get_client_by_telegram_id(message.from_user.id)
        if not client:
            await message.answer("Вы ещё не зарегистрированы. Нажмите /start")
            return
        cars = await client_service.get_client_cars(client.id)

    if not cars:
        await message.answer("Сначала добавьте автомобиль! Нажмите «➕ Добавить авто»")
        return

    await state.update_data(client_id=str(client.id))
    await message.answer(SERVICE_SELECTION, reply_markup=service_categories_keyboard())
    await state.set_state(BookingStates.selecting_category)


@router.callback_query(BookingStates.selecting_category, F.data.startswith("cat:"))
async def select_category(callback: CallbackQuery, state: FSMContext) -> None:
    category = callback.data.split(":", 1)[1]

    async with async_session_factory() as session:
        from sqlalchemy import select
        result = await session.execute(select(Service).where(Service.category == category))
        services = list(result.scalars().all())

    if not services:
        await callback.message.answer("В данной категории пока нет услуг.")
        await state.clear()
        return

    svc_list = [(s.name, str(s.id)) for s in services]
    await callback.message.answer("Выберите услугу:", reply_markup=services_keyboard(svc_list))
    await state.set_state(BookingStates.selecting_service)


@router.callback_query(BookingStates.selecting_service, F.data.startswith("svc:"))
async def select_service(callback: CallbackQuery, state: FSMContext) -> None:
    service_id = callback.data.split(":", 1)[1]

    async with async_session_factory() as session:
        service = await session.get(Service, service_id)
        if not service:
            await callback.message.answer("Услуга не найдена.")
            await state.clear()
            return

    await state.update_data(service_id=service_id, duration=service.duration_minutes, requires_lift=service.requires_lift)

    data = await state.get_data()
    client_id = data["client_id"]

    async with async_session_factory() as session:
        client_service = ClientProfileService(session)
        cars = await client_service.get_client_cars(client_id)

    car_list = [(f"{c.brand} {c.model} ({c.license_plate})", str(c.id)) for c in cars]
    await callback.message.answer("Выберите автомобиль:", reply_markup=cars_keyboard(car_list))
    await state.set_state(BookingStates.selecting_car)


@router.callback_query(BookingStates.selecting_car, F.data.startswith("car:"))
async def select_car(callback: CallbackQuery, state: FSMContext) -> None:
    car_id = callback.data.split(":", 1)[1]
    await state.update_data(car_id=car_id)

    today = datetime.date.today()
    dates = []
    for i in range(14):
        d = today + datetime.timedelta(days=i)
        if d.weekday() in [0, 1, 2, 3, 4, 5]:
            dates.append(d.strftime("%d.%m.%Y"))

    await callback.message.answer(DATE_SELECTION, reply_markup=dates_keyboard(dates))
    await state.set_state(BookingStates.selecting_date)


@router.callback_query(BookingStates.selecting_date, F.data.startswith("date:"))
async def select_date(callback: CallbackQuery, state: FSMContext) -> None:
    date_str = callback.data.split(":", 1)[1]
    date_obj = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()

    data = await state.get_data()
    duration = data["duration"]
    requires_lift = data["requires_lift"]

    async with async_session_factory() as session:
        availability_service = AvailabilityService(session)
        slots = await availability_service.get_available_slots(
            date=date_obj,
            service_duration_minutes=duration,
            requires_lift=requires_lift,
        )

    available_slots = [s for s in slots if s["available"]]
    if not available_slots:
        await callback.message.answer(NO_SLOTS_AVAILABLE)
        return

    await state.update_data(selected_date=date_str)
    await callback.message.answer(TIME_SELECTION, reply_markup=time_slots_keyboard(available_slots, date_str))
    await state.set_state(BookingStates.selecting_time)


@router.callback_query(BookingStates.selecting_time, F.data.startswith("slot:"))
async def select_time(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    date_str = parts[1]
    time_str = parts[2]

    data = await state.get_data()

    date_obj = datetime.datetime.strptime(date_str, "%d.%m.%Y").date()
    time_obj = datetime.datetime.strptime(time_str, "%H:%M").time()

    async with async_session_factory() as session:
        service = await session.get(Service, data["service_id"])

    text = (
        f"📋 Подтверждение записи:\n\n"
        f"📅 Дата: {date_str}\n"
        f"🕐 Время: {time_str}\n"
        f"🔧 Услуга: {service.name}\n"
        f"⏱ Длительность: {service.duration_minutes} мин\n\n"
        f"Подтвердите запись?"
    )

    await state.update_data(start_time=time_str, selected_date_iso=date_obj.isoformat())
    await callback.message.answer(text, reply_markup=confirm_keyboard("pending"))
    await state.set_state(BookingStates.confirming)


@router.callback_query(BookingStates.confirming, F.data.startswith("confirm:"))
async def confirm_booking(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()

    date_obj = datetime.date.fromisoformat(data["selected_date_iso"])
    time_obj = datetime.datetime.strptime(data["start_time"], "%H:%M").time()

    from src.schemas.appointment import AppointmentCreate
    appointment_data = AppointmentCreate(
        client_id=data["client_id"],
        car_id=data["car_id"],
        service_id=data["service_id"],
        date=date_obj,
        start_time=time_obj,
    )

    async with async_session_factory() as session:
        booking_service = BookingService(session)
        try:
            appointment = await booking_service.create_appointment(appointment_data)
            await session.commit()
        except ValueError as e:
            await callback.message.answer(f"⚠️ Ошибка: {e}")
            await state.clear()
            return

        service = await session.get(Service, appointment.service_id)

    await callback.message.answer(
        APPOINTMENT_CONFIRMED.format(
            date=date_obj.strftime("%d.%m.%Y"),
            time=time_obj.strftime("%H:%M"),
            service=service.name,
            car=data.get("car_id", ""),
        ),
        reply_markup=main_menu_keyboard(),
    )
    await state.clear()


@router.callback_query(BookingStates.confirming, F.data.startswith("cancel:"))
async def cancel_booking_process(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.message.answer("Запись отменена.", reply_markup=main_menu_keyboard())
    await state.clear()
