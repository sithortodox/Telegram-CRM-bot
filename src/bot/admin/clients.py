import uuid

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.database import async_session_factory
from src.services.client_profile import ClientProfileService
from src.bot.common.filters import AdminFilter

router = Router(name="admin_clients")


class ClientSearchStates(StatesGroup):
    waiting_for_query = State()


@router.message(AdminFilter(), F.text == "👥 Клиенты")
async def clients_menu(message: Message) -> None:
    async with async_session_factory() as session:
        client_service = ClientProfileService(session)
        clients = await client_service.get_all_clients()

    if not clients:
        await message.answer("👥 База клиентов пуста.")
        return

    text = f"👥 Всего клиентов: {len(clients)}\n\n"
    for c in clients[:20]:
        text += f"• {c.full_name} | 📱 {c.phone}\n"

    if len(clients) > 20:
        text += f"\n...и ещё {len(clients) - 20} клиентов"

    await message.answer(text + "\n\nДля поиска введите: /search Имя или телефон")


@router.message(AdminFilter(), F.text.startswith("/search "))
async def search_clients(message: Message) -> None:
    query = message.text[8:].strip()
    if not query:
        await message.answer("⚠️ Введите запрос: /search Имя или телефон")
        return

    async with async_session_factory() as session:
        client_service = ClientProfileService(session)
        clients = await client_service.search_clients(query)

    if not clients:
        await message.answer("🔍 Клиенты не найдены.")
        return

    for client in clients:
        profile = await client_service.get_client_with_history(client.id)
        text = (
            f"👤 {client.full_name}\n"
            f"📱 {client.phone}\n"
            f"📋 Визитов: {profile['total_visits']}\n"
        )
        if profile["average_rating"]:
            text += f"⭐ Средняя оценка: {profile['average_rating']:.1f}\n"
        for car in profile["cars"]:
            text += f"🚗 {car.brand} {car.model} ({car.year}) — {car.license_plate}\n"

        await message.answer(text)
