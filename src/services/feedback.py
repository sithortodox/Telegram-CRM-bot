import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.feedback import Feedback
from src.schemas.feedback import FeedbackCreate


class FeedbackService:
    """Сервис отзывов и оценок"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_feedback(self, data: FeedbackCreate) -> Feedback:
        existing = await self.session.execute(
            select(Feedback).where(Feedback.appointment_id == data.appointment_id)
        )
        if existing.scalar_one_or_none():
            raise ValueError("Отзыв на эту запись уже существует")

        feedback = Feedback(
            appointment_id=data.appointment_id,
            client_id=data.client_id,
            rating=data.rating,
            comment=data.comment,
        )
        self.session.add(feedback)
        await self.session.flush()
        return feedback

    async def get_client_feedbacks(self, client_id: uuid.UUID) -> list[Feedback]:
        query = (
            select(Feedback)
            .where(Feedback.client_id == client_id)
            .order_by(Feedback.created_at.desc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_appointment_feedback(self, appointment_id: uuid.UUID) -> Feedback | None:
        query = select(Feedback).where(Feedback.appointment_id == appointment_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_average_rating(self) -> float:
        from sqlalchemy import func
        query = select(func.avg(Feedback.rating))
        result = await self.session.execute(query)
        avg = result.scalar()
        return float(avg) if avg else 0.0
