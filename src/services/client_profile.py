import uuid

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.car import Car
from src.models.client import Client
from src.models.appointment import Appointment
from src.schemas.client import ClientCreate, ClientUpdate


class ClientProfileService:
    """Сервис профилей клиентов"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def register_client(self, data: ClientCreate) -> Client:
        existing = await self.get_client_by_telegram_id(data.telegram_id)
        if existing:
            raise ValueError("Клиент с таким Telegram ID уже зарегистрирован")

        client = Client(
            telegram_id=data.telegram_id,
            username=data.username,
            full_name=data.full_name,
            phone=data.phone,
            data_consent=data.data_consent,
            data_consent_at=__import__("datetime").datetime.now() if data.data_consent else None,
        )
        self.session.add(client)
        await self.session.flush()
        return client

    async def update_client(self, client_id: uuid.UUID, data: ClientUpdate) -> Client:
        client = await self._get_client(client_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(client, field, value)
        await self.session.flush()
        return client

    async def get_client_by_telegram_id(self, telegram_id: int) -> Client | None:
        query = select(Client).where(Client.telegram_id == telegram_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_client_with_history(self, client_id: uuid.UUID) -> dict:
        """Карточка клиента с историей визитов и оценок"""
        client = await self._get_client(client_id)

        cars_query = select(Car).where(Car.client_id == client_id)
        cars_result = await self.session.execute(cars_query)
        cars = list(cars_result.scalars().all())

        appointments_query = (
            select(Appointment)
            .where(Appointment.client_id == client_id)
            .order_by(Appointment.date.desc())
        )
        appointments_result = await self.session.execute(appointments_query)
        appointments = list(appointments_result.scalars().all())

        total_visits = len(appointments)
        from src.models.feedback import Feedback
        avg_rating_query = select(func.avg(Feedback.rating)).where(Feedback.client_id == client_id)
        avg_rating_result = await self.session.execute(avg_rating_query)
        avg_rating = avg_rating_result.scalar()

        return {
            "client": client,
            "cars": cars,
            "appointments": appointments,
            "total_visits": total_visits,
            "average_rating": float(avg_rating) if avg_rating else None,
        }

    async def get_client_cars(self, client_id: uuid.UUID) -> list[Car]:
        query = select(Car).where(Car.client_id == client_id)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def add_car(self, client_id: uuid.UUID, brand: str, model: str, year: int, license_plate: str, vin: str | None = None) -> Car:
        car = Car(
            client_id=client_id,
            brand=brand,
            model=model,
            year=year,
            license_plate=license_plate,
            vin=vin,
        )
        self.session.add(car)
        await self.session.flush()
        return car

    async def search_clients(self, query_text: str) -> list[Client]:
        search = f"%{query_text}%"
        query = select(Client).where(
            (Client.full_name.ilike(search)) | (Client.phone.ilike(search))
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_all_clients(self) -> list[Client]:
        query = select(Client).order_by(Client.full_name)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _get_client(self, client_id: uuid.UUID) -> Client:
        client = await self.session.get(Client, client_id)
        if not client:
            raise ValueError("Клиент не найден")
        return client
