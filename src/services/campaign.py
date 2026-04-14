import datetime
import logging
import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.client import Client
from src.models.marketing_campaign import MarketingCampaign
from src.schemas.campaign import CampaignCreate


logger = logging.getLogger(__name__)


class CampaignService:
    """Сервис маркетинговых рассылок"""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_campaign(self, data: CampaignCreate) -> MarketingCampaign:
        campaign = MarketingCampaign(
            name=data.name,
            message_text=data.message_text,
            target_filter=data.target_filter,
            scheduled_at=data.scheduled_at,
        )
        self.session.add(campaign)
        await self.session.flush()
        return campaign

    async def start_campaign(self, campaign_id: uuid.UUID) -> MarketingCampaign:
        """Запуск рассылки"""
        campaign = await self._get_campaign(campaign_id)
        if campaign.status != "draft":
            raise ValueError("Рассылка уже запущена или завершена")

        clients = await self._get_target_clients(campaign.target_filter)
        campaign.total_recipients = len(clients)
        campaign.status = "in_progress"
        campaign.started_at = datetime.datetime.now()

        await self.session.flush()
        return campaign

    async def complete_campaign(self, campaign_id: uuid.UUID) -> MarketingCampaign:
        campaign = await self._get_campaign(campaign_id)
        campaign.status = "completed"
        campaign.completed_at = datetime.datetime.now()
        await self.session.flush()
        return campaign

    async def get_campaign_recipients(self, campaign_id: uuid.UUID) -> list[Client]:
        """Получение списка получателей рассылки"""
        campaign = await self._get_campaign(campaign_id)
        return await self._get_target_clients(campaign.target_filter)

    async def get_all_campaigns(self) -> list[MarketingCampaign]:
        query = select(MarketingCampaign).order_by(MarketingCampaign.created_at.desc())
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _get_target_clients(self, target_filter: str | None) -> list[Client]:
        """Фильтрация клиентов по критериям рассылки"""
        query = select(Client)
        if target_filter:
            query = query.where(Client.data_consent.is_(True))
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def _get_campaign(self, campaign_id: uuid.UUID) -> MarketingCampaign:
        campaign = await self.session.get(MarketingCampaign, campaign_id)
        if not campaign:
            raise ValueError("Рассылка не найдена")
        return campaign
