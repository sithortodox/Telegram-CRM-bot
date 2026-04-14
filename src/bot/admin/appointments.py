import uuid

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.database import async_session_factory
from src.services.booking import BookingService
from src.config import AppointmentStatusEnum
from src.bot.common.filters import ManagerFilter
from src.bot.common.keyboards import InlineKeyboardMarkup, InlineKeyboardButton

router = Router(name="admin_appointments")


class ManualBookingStates(StatesGroup):
    waiting_for_client_phone = State()
    waiting_for_service = State()
    waiting_for_date_time = State()


@router.message(ManagerFilter(), F.text.startswith("/cancel_apt "))
async def admin_cancel_appointment(message: Message) -> None:
    try:
        appointment_id = uuid.UUID(message.text[12:].strip())
    except ValueError:
        await message.answer("⚠️ Неверный формат ID записи.")
        return

    async with async_session_factory() as session:
        booking_service = BookingService(session)
        try:
            await booking_service.cancel_by_admin(appointment_id, f"admin_{message.from_user.id}")
            await session.commit()
        except ValueError as e:
            await message.answer(f"⚠️ {e}")
            return

    await message.answer("✅ Запись отменена администратором.")


@router.message(ManagerFilter(), F.text.startswith("/noshow "))
async def mark_no_show(message: Message) -> None:
    try:
        appointment_id = uuid.UUID(message.text[8:].strip())
    except ValueError:
        await message.answer("⚠️ Неверный формат ID записи.")
        return

    async with async_session_factory() as session:
        booking_service = BookingService(session)
        try:
            await booking_service.mark_no_show(appointment_id, f"admin_{message.from_user.id}")
            await session.commit()
        except ValueError as e:
            await message.answer(f"⚠️ {e}")
            return

    await message.answer("✅ Клиент отмечен как «не явился».")


@router.message(ManagerFilter(), F.text.startswith("/complete_apt "))
async def complete_appointment(message: Message) -> None:
    try:
        appointment_id = uuid.UUID(message.text[14:].strip())
    except ValueError:
        await message.answer("⚠️ Неверный формат ID записи.")
        return

    async with async_session_factory() as session:
        booking_service = BookingService(session)
        try:
            await booking_service.complete_appointment(appointment_id)
            await session.commit()
        except ValueError as e:
            await message.answer(f"⚠️ {e}")
            return

    await message.answer("✅ Визит отмечен как завершённый.")
