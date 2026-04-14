from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.database import async_session_factory
from src.services.client_profile import ClientProfileService
from src.bot.common.keyboards import main_menu_keyboard
from src.bot.common.texts import WELCOME, REGISTRATION_PROMPT, DATA_CONSENT

router = Router(name="client_registration")


class RegistrationStates(StatesGroup):
    waiting_for_name_phone = State()
    waiting_for_consent = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext) -> None:
    async with async_session_factory() as session:
        client_service = ClientProfileService(session)
        client = await client_service.get_client_by_telegram_id(message.from_user.id)

    if client:
        await message.answer(WELCOME, reply_markup=main_menu_keyboard())
    else:
        await message.answer(REGISTRATION_PROMPT)
        await state.set_state(RegistrationStates.waiting_for_name_phone)


@router.message(RegistrationStates.waiting_for_name_phone)
async def process_name_phone(message: Message, state: FSMContext) -> None:
    parts = [p.strip() for p in message.text.split("|")]
    if len(parts) < 2:
        await message.answer("⚠️ Неверный формат. Используйте: Имя | Телефон")
        return

    full_name = parts[0]
    phone = parts[1]

    await state.update_data(full_name=full_name, phone=phone)

    from src.bot.common.keyboards import InlineKeyboardMarkup, InlineKeyboardButton
    consent_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Согласен", callback_data="consent:yes"),
         InlineKeyboardButton(text="❌ Не согласен", callback_data="consent:no")]
    ])
    await message.answer(DATA_CONSENT, reply_markup=consent_kb)
    await state.set_state(RegistrationStates.waiting_for_consent)


@router.callback_query(RegistrationStates.waiting_for_consent, F.data.startswith("consent:"))
async def process_consent(callback: CallbackQuery, state: FSMContext) -> None:
    consent = callback.data == "consent:yes"

    if not consent:
        await callback.message.answer("❌ Без согласия на обработку данных регистрация невозможна.")
        await state.clear()
        return

    data = await state.get_data()
    async with async_session_factory() as session:
        client_service = ClientProfileService(session)
        try:
            await client_service.register_client(
                type("ClientData", (), {
                    "telegram_id": callback.from_user.id,
                    "username": callback.from_user.username,
                    "full_name": data["full_name"],
                    "phone": data["phone"],
                    "data_consent": True,
                })()
            )
            await session.commit()
        except ValueError as e:
            await callback.message.answer(f"⚠️ {e}")
            await state.clear()
            return

    await callback.message.answer(WELCOME, reply_markup=main_menu_keyboard())
    await state.clear()
