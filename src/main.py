import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from src.config import settings
from src.utils.logging import setup_logging, get_logger
from src.bot.router import get_main_router
from src.scheduler.tasks import setup_scheduler, scheduler
from src.api.app import app as fastapi_app

logger = get_logger("main")


async def main() -> None:
    setup_logging(settings.log_level)
    logger.info("starting_bot")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.include_router(get_main_router())

    setup_scheduler()
    scheduler.start()
    logger.info("scheduler_started")

    from src.database import engine
    from src.models.base import Base
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("database_tables_created")

    try:
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("bot_stopped")
