from aiogram import Router

from src.bot.client.registration import router as registration_router
from src.bot.client.car import router as car_router
from src.bot.client.booking import router as booking_router
from src.bot.client.cancellation import router as cancellation_router
from src.bot.client.feedback import router as feedback_router
from src.bot.client.profile import router as profile_router
from src.bot.admin.schedule import router as schedule_router
from src.bot.admin.clients import router as clients_router
from src.bot.admin.appointments import router as appointments_router
from src.bot.admin.slots import router as slots_router
from src.bot.admin.campaigns import router as campaigns_router
from src.bot.admin.analytics import router as analytics_router


def get_main_router() -> Router:
    """Сборка главного роутера из всех подроутеров"""
    router = Router(name="main")

    router.include_router(registration_router)
    router.include_router(car_router)
    router.include_router(booking_router)
    router.include_router(cancellation_router)
    router.include_router(feedback_router)
    router.include_router(profile_router)
    router.include_router(schedule_router)
    router.include_router(clients_router)
    router.include_router(appointments_router)
    router.include_router(slots_router)
    router.include_router(campaigns_router)
    router.include_router(analytics_router)

    return router
