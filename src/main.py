# src/main.py
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from src.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    settings = get_settings()
    logger.info(
        "%s | env=%s | debug=%s — startup complete",
        settings.APP_NAME,
        settings.APP_ENVIRONMENT,
        settings.APP_DEBUG,
    )
    yield
    logger.info("%s — shutdown complete", settings.APP_NAME)


app = FastAPI(title="ChatOps Incident Agent", lifespan=lifespan)
