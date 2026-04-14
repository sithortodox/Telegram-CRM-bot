import datetime

from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.database import async_session_factory
from src.services.lift_allocation import LiftAllocationService
from src.services.staff_assignment import StaffAssignmentService
from src.bot.common.filters import AdminFilter
from src.bot.common.keyboards import InlineKeyboardMarkup, InlineKeyboardButton

router = Router(name="admin_slots")


class BlockSlotStates(StatesGroup):
    selecting_resource = State()
    entering_date_time = State()
    entering_reason = State()


@router.message(AdminFilter(), F.text == "🏗 Подъемники")
async def lifts_menu(message: Message) -> None:
    async with async_session_factory() as session:
        lift_service = LiftAllocationService(session)
        lifts = await lift_service.get_all_lifts(active_only=False)

    if not lifts:
        await message.answer("🏗 Подъемники не настроены. Добавьте через /add_lift Название")
        return

    text = "🏗 Подъемники:\n\n"
    for lift in lifts:
        status = "✅ Активен" if lift.is_active else "❌ Неактивен"
        text += f"• {lift.name} ({lift.lift_type}) — {status}\n"

    await message.answer(text)


@router.message(AdminFilter(), F.text == "🔧 Мастера")
async def masters_menu(message: Message) -> None:
    async with async_session_factory() as session:
        staff_service = StaffAssignmentService(session)
        masters = await staff_service.get_all_masters(active_only=False)

    if not masters:
        await message.answer("🔧 Мастера не настроены. Добавьте через /add_master Имя")
        return

    text = "🔧 Мастера:\n\n"
    for m in masters:
        status = "✅ Активен" if m.is_active else "❌ Неактивен"
        spec = f" ({m.specializations})" if m.specializations else ""
        text += f"• {m.full_name}{spec} — {status}\n"

    await message.answer(text)


@router.message(AdminFilter(), F.text.startswith("/add_master "))
async def add_master(message: Message) -> None:
    full_name = message.text[12:].strip()
    if not full_name:
        await message.answer("⚠️ Укажите имя: /add_master Иван Иванов")
        return

    from src.schemas.staff import StaffCreate
    async with async_session_factory() as session:
        staff_service = StaffAssignmentService(session)
        master = await staff_service.create_staff(StaffCreate(full_name=full_name))
        await session.commit()

    await message.answer(f"✅ Мастер {full_name} добавлен.")


@router.message(AdminFilter(), F.text.startswith("/add_lift "))
async def add_lift(message: Message) -> None:
    name = message.text[10:].strip()
    if not name:
        await message.answer("⚠️ Укажите название: /add_lift Подъемник 1")
        return

    from src.models.lift import Lift
    async with async_session_factory() as session:
        lift = Lift(name=name)
        session.add(lift)
        await session.commit()

    await message.answer(f"✅ Подъемник «{name}» добавлен.")


@router.message(AdminFilter(), F.text.startswith("/block_lift "))
async def block_lift_prompt(message: Message, state: FSMContext) -> None:
    """Формат: /block_lift Название | Дата | Причина"""
    parts = [p.strip() for p in message.text[12:].split("|")]
    if len(parts) < 3:
        await message.answer("⚠️ Формат: /block_lift Название | ДД.ММ.ГГГГ | Причина")
        return

    try:
        date = datetime.datetime.strptime(parts[1], "%d.%m.%Y").date()
    except ValueError:
        await message.answer("⚠️ Неверный формат даты. Используйте ДД.ММ.ГГГГ")
        return

    async with async_session_factory() as session:
        from sqlalchemy import select
        from src.models.lift import Lift
        result = await session.execute(select(Lift).where(Lift.name == parts[0]))
        lift = result.scalar_one_or_none()

        if not lift:
            await message.answer("⚠️ Подъемник не найден.")
            return

        lift_service = LiftAllocationService(session)
        await lift_service.block_lift(
            lift_id=lift.id,
            date=date,
            start_time=datetime.time(9, 0),
            end_time=datetime.time(21, 0),
            reason=parts[2],
        )
        await session.commit()

    await message.answer(f"✅ Подъемник «{parts[0]}» заблокирован на {parts[1]}.")


@router.message(AdminFilter(), F.text.startswith("/deactivate_master "))
async def deactivate_master(message: Message) -> None:
    full_name = message.text[19:].strip()
    async with async_session_factory() as session:
        from sqlalchemy import select
        from src.models.staff import Staff
        result = await session.execute(select(Staff).where(Staff.full_name == full_name, Staff.role == "master"))
        master = result.scalar_one_or_none()
        if not master:
            await message.answer("⚠️ Мастер не найден.")
            return
        staff_service = StaffAssignmentService(session)
        await staff_service.deactivate_staff(master.id)
        await session.commit()

    await message.answer(f"✅ Мастер {full_name} деактивирован.")
