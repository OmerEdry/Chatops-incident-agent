# src/main.py
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

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
