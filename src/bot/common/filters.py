from aiogram.filters import Filter
from aiogram.types import Message

from src.config import settings
from src.models.staff import Staff
from src.database import async_session_factory


class OwnerFilter(Filter):
    """Фильтр: только владелец"""

    async def __call__(self, message: Message) -> bool:
        return message.from_user.id in settings.owner_ids_list


class AdminFilter(Filter):
    """Фильтр: администратор и выше"""

    async def __call__(self, message: Message) -> bool:
        if message.from_user.id in settings.owner_ids_list:
            return True
        async with async_session_factory() as session:
            from sqlalchemy import select
            query = select(Staff).where(
                Staff.telegram_id == message.from_user.id,
                Staff.is_active.is_(True),
                Staff.role.in_(["owner", "admin"]),
            )
            result = await session.execute(query)
            return result.scalar_one_or_none() is not None


class ManagerFilter(Filter):
    """Фильтр: менеджер и выше"""

    async def __call__(self, message: Message) -> bool:
        if message.from_user.id in settings.owner_ids_list:
            return True
        async with async_session_factory() as session:
            from sqlalchemy import select
            query = select(Staff).where(
                Staff.telegram_id == message.from_user.id,
                Staff.is_active.is_(True),
                Staff.role.in_(["owner", "admin", "manager"]),
            )
            result = await session.execute(query)
            return result.scalar_one_or_none() is not None


class MasterFilter(Filter):
    """Фильтр: мастер"""

    async def __call__(self, message: Message) -> bool:
        if message.from_user.id in settings.owner_ids_list:
            return True
        async with async_session_factory() as session:
            from sqlalchemy import select
            query = select(Staff).where(
                Staff.telegram_id == message.from_user.id,
                Staff.is_active.is_(True),
            )
            result = await session.execute(query)
            return result.scalar_one_or_none() is not None


class MarketingFilter(Filter):
    """Фильтр: маркетолог и выше"""

    async def __call__(self, message: Message) -> bool:
        if message.from_user.id in settings.owner_ids_list:
            return True
        async with async_session_factory() as session:
            from sqlalchemy import select
            query = select(Staff).where(
                Staff.telegram_id == message.from_user.id,
                Staff.is_active.is_(True),
                Staff.role.in_(["owner", "admin", "marketing"]),
            )
            result = await session.execute(query)
            return result.scalar_one_or_none() is not None
