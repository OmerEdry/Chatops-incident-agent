# src/db/engine.py
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import get_settings
from src.db.models import Base

logger = logging.getLogger(__name__)

_settings = get_settings()

engine = create_async_engine(
    _settings.database_url,
    echo=_settings.APP_DEBUG,
    pool_size=5,
    max_overflow=10,
)

AsyncSessionFactory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    engine, expire_on_commit=False
)


async def init_db() -> None:
    """Create all tables if they do not exist. Intended for dev startup only.

    In production, table creation is handled by Alembic migrations.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database schema verified/initialized.")


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Yield a transactional AsyncSession, committing on success or rolling back on error."""
    async with AsyncSessionFactory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def verify_schema() -> bool:
    """Health-check: confirm the incidents table is reachable.

    Demonstrates an asyncpg-backed parameterized query via SQLAlchemy text().
    Returns True if the table exists and is queryable, False otherwise.
    """
    try:
        async with engine.connect() as conn:
            # text() with bound params is SQLAlchemy's parameterized query mechanism;
            # asyncpg translates this to a $1-style prepared statement under the hood.
            result = await conn.execute(
                text("SELECT 1 FROM incidents LIMIT :limit"), {"limit": 1}
            )
            result.close()
        logger.info("Schema verification passed — incidents table is reachable.")
        return True
    except OperationalError as exc:
        logger.error("Schema verification failed: %s", exc)
        return False
