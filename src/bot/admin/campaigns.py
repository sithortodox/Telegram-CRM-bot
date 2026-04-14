from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from src.database import async_session_factory
from src.services.campaign import CampaignService
from src.bot.common.filters import MarketingFilter
from src.bot.common.keyboards import InlineKeyboardMarkup, InlineKeyboardButton

router = Router(name="admin_campaigns")


class CampaignStates(StatesGroup):
    entering_name = State()
    entering_message = State()
    confirming = State()


@router.message(MarketingFilter(), F.text == "📢 Рассылки")
async def campaigns_menu(message: Message) -> None:
    async with async_session_factory() as session:
        campaign_service = CampaignService(session)
        campaigns = await campaign_service.get_all_campaigns()

    if not campaigns:
        await message.answer("📢 Нет рассылок. Создайте через /new_campaign")
        return

    text = "📢 Рассылки:\n\n"
    for c in campaigns:
        text += f"• {c.name} — {c.status} ({c.sent_count}/{c.total_recipients})\n"

    await message.answer(text)


@router.message(MarketingFilter(), F.text.startswith("/new_campaign "))
async def new_campaign(message: Message, state: FSMContext) -> None:
    parts = [p.strip() for p in message.text[15:].split("|")]
    if len(parts) < 2:
        await message.answer("⚠️ Формат: /new_campaign Название | Текст рассылки")
        return

    from src.schemas.campaign import CampaignCreate
    async with async_session_factory() as session:
        campaign_service = CampaignService(session)
        campaign = await campaign_service.create_campaign(CampaignCreate(
            name=parts[0],
            message_text=parts[1],
        ))
        await session.commit()

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Запустить", callback_data=f"start_campaign:{campaign.id}")],
    ])
    await message.answer(f"✅ Рассылка «{parts[0]}» создана (черновик).", reply_markup=kb)


@router.callback_query(MarketingFilter(), F.data.startswith("start_campaign:"))
async def start_campaign(callback: CallbackQuery) -> None:
    import uuid
    campaign_id = uuid.UUID(callback.data.split(":")[1])

    async with async_session_factory() as session:
        campaign_service = CampaignService(session)
        try:
            campaign = await campaign_service.start_campaign(campaign_id)
            await session.commit()
        except ValueError as e:
            await callback.message.answer(f"⚠️ {e}")
            return

    await callback.message.answer(
        f"🚀 Рассылка «{campaign.name}» запущена!\n"
        f"Получателей: {campaign.total_recipients}"
    )
