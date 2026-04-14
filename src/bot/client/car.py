from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.database import async_session_factory
from src.services.client_profile import ClientProfileService
from src.bot.common.keyboards import cars_keyboard, back_to_main_keyboard
from src.bot.common.texts import ADD_CAR_PROMPT, MY_CARS_EMPTY

router = Router(name="client_car")


class CarStates(StatesGroup):
    waiting_for_car_info = State()
    waiting_for_vin = State()


@router.message(F.text == "🚗 Мои автомобили")
async def my_cars(message: Message) -> None:
    async with async_session_factory() as session:
        client_service = ClientProfileService(session)
        client = await client_service.get_client_by_telegram_id(message.from_user.id)
        if not client:
            await message.answer("Вы ещё не зарегистрированы. Нажмите /start")
            return
        cars = await client_service.get_client_cars(client.id)

    if not cars:
        await message.answer(MY_CARS_EMPTY + "\n\n" + ADD_CAR_PROMPT)
        return

    text = "🚗 Ваши автомобили:\n\n"
    for car in cars:
        text += f"• {car.brand} {car.model} ({car.year}) — {car.license_plate}"
        if car.vin:
            text += f"\n  VIN: {car.vin}"
        text += "\n"

    await message.answer(text)


@router.message(F.text == "➕ Добавить авто")
async def add_car_prompt(message: Message, state: FSMContext) -> None:
    await message.answer(ADD_CAR_PROMPT)
    await state.set_state(CarStates.waiting_for_car_info)


@router.message(CarStates.waiting_for_car_info)
async def process_car_info(message: Message, state: FSMContext) -> None:
    parts = [p.strip() for p in message.text.split("|")]
    if len(parts) < 4:
        await message.answer("⚠️ Неверный формат. Используйте: Марка | Модель | Год | Госномер")
        return

    try:
        year = int(parts[2])
    except ValueError:
        await message.answer("⚠️ Год должен быть числом.")
        return

    async with async_session_factory() as session:
        client_service = ClientProfileService(session)
        client = await client_service.get_client_by_telegram_id(message.from_user.id)
        if not client:
            await message.answer("Вы ещё не зарегистрированы. Нажмите /start")
            await state.clear()
            return

        try:
            car = await client_service.add_car(
                client_id=client.id,
                brand=parts[0],
                model=parts[1],
                year=year,
                license_plate=parts[3],
                vin=parts[4] if len(parts) > 4 else None,
            )
            await session.commit()
        except Exception as e:
            await message.answer(f"⚠️ Ошибка: {e}")
            await state.clear()
            return

    await message.answer(f"✅ Автомобиль {car.brand} {car.model} добавлен!")
    await state.clear()
