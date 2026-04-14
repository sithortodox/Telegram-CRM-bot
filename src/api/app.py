from fastapi import FastAPI

from src.utils.logging import get_logger

logger = get_logger("api")

app = FastAPI(
    title="Telegram CRM Автосервис",
    description="API для Telegram CRM-бота автосервиса",
    version="1.0.0",
)


@app.get("/health")
async def health_check() -> dict:
    return {"status": "ok", "service": "telegram-crm-autoservice"}


@app.post("/webhook")
async def webhook_handler() -> dict:
    return {"status": "ok"}
