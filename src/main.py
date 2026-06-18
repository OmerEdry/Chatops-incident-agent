# src/main.py
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI

from src.api.routes import router
from src.core.config import get_settings
from src.db import init_db

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info(
        "%s | env=%s | debug=%s — starting up",
        settings.APP_NAME,
        settings.APP_ENVIRONMENT,
        settings.APP_DEBUG,
    )
    try:
        await init_db()
    except Exception as exc:
        logger.critical(
            "Database initialisation failed — cannot start %s: %s",
            settings.APP_NAME,
            exc,
            exc_info=True,
        )
        raise
    logger.info("%s — startup complete", settings.APP_NAME)
    yield
    logger.info("%s — shutdown complete", settings.APP_NAME)


app = FastAPI(title="ChatOps Incident Agent", lifespan=lifespan)

app.include_router(router)


@app.get("/api/v1/health")
async def health_check() -> dict[str, str]:
    return {"status": "ok", "service": "chatops-agent"}


if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
