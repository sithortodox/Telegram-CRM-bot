from aiogram import Router, F
from aiogram.types import Message

from src.database import async_session_factory
from src.services.client_profile import ClientProfileService
from src.bot.common.keyboards import main_menu_keyboard

router = Router(name="client_profile")


@router.message(F.text == "👤 Мой профиль")
async def my_profile(message: Message) -> None:
    async with async_session_factory() as session:
        client_service = ClientProfileService(session)
        client = await client_service.get_client_by_telegram_id(message.from_user.id)
        if not client:
            await message.answer("Вы ещё не зарегистрированы. Нажмите /start")
            return

        profile = await client_service.get_client_with_history(client.id)

    client = profile["client"]
    cars = profile["cars"]
    total_visits = profile["total_visits"]
    avg_rating = profile["average_rating"]

    text = (
        f"👤 Ваш профиль:\n\n"
        f"📌 Имя: {client.full_name}\n"
        f"📱 Телефон: {client.phone}\n"
        f"🚗 Автомобилей: {len(cars)}\n"
        f"📋 Всего визитов: {total_visits}\n"
    )
    if avg_rating is not None:
        text += f"⭐ Средняя оценка: {avg_rating:.1f}\n"

    if cars:
        text += "\n🚗 Ваши авто:\n"
        for car in cars:
            text += f"  • {car.brand} {car.model} ({car.year}) — {car.license_plate}\n"

    await message.answer(text)
