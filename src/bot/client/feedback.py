import uuid

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.database import async_session_factory
from src.services.feedback import FeedbackService
from src.services.booking import BookingService
from src.services.client_profile import ClientProfileService
from src.bot.common.keyboards import rating_keyboard
from src.bot.common.texts import FEEDBACK_REQUEST, FEEDBACK_COMMENT_PROMPT, FEEDBACK_THANKS

router = Router(name="client_feedback")


class FeedbackStates(StatesGroup):
    waiting_for_rating = State()
    waiting_for_comment = State()


@router.message(F.text == "⭐ Оставить отзыв")
async def request_feedback_menu(message: Message) -> None:
    async with async_session_factory() as session:
        client_service = ClientProfileService(session)
        client = await client_service.get_client_by_telegram_id(message.from_user.id)
        if not client:
            await message.answer("Вы ещё не зарегистрированы. Нажмите /start")
            return

        from src.services.reminder import ReminderService
        reminder_service = ReminderService(session)
        completed = await reminder_service.get_completed_without_feedback()

        client_completed = [a for a in completed if a.client_id == client.id]

    if not client_completed:
        await message.answer("У вас нет завершённых визитов без отзыва.")
        return

    latest = client_completed[0]
    await state_update_feedback(message, str(latest.id), FeedbackStates.waiting_for_rating)


async def state_update_feedback(message: Message, appointment_id: str, next_state) -> None:
    from aiogram.fsm.context import FSMContext
    pass


@router.callback_query(F.data.startswith("rate:"))
async def process_rating(callback: CallbackQuery, state: FSMContext) -> None:
    parts = callback.data.split(":")
    appointment_id = parts[1]
    rating = int(parts[2])

    await state.update_data(appointment_id=appointment_id, rating=rating)
    await callback.message.answer(FEEDBACK_COMMENT_PROMPT)
    await state.set_state(FeedbackStates.waiting_for_comment)


@router.message(FeedbackStates.waiting_for_comment)
async def process_feedback_comment(message: Message, state: FSMContext) -> None:
    data = await state.get_data()
    appointment_id = uuid.UUID(data["appointment_id"])
    rating = data["rating"]

    comment = None
    if message.text and message.text != "/skip":
        comment = message.text

    async with async_session_factory() as session:
        from src.models.appointment import Appointment
        appointment = await session.get(Appointment, appointment_id)
        if not appointment:
            await message.answer("⚠️ Запись не найдена.")
            await state.clear()
            return

        feedback_service = FeedbackService(session)
        try:
            from src.schemas.feedback import FeedbackCreate
            await feedback_service.create_feedback(FeedbackCreate(
                appointment_id=appointment_id,
                client_id=appointment.client_id,
                rating=rating,
                comment=comment,
            ))
            await session.commit()
        except ValueError as e:
            await message.answer(f"⚠️ {e}")
            await state.clear()
            return

    await message.answer(FEEDBACK_THANKS)
    await state.clear()
