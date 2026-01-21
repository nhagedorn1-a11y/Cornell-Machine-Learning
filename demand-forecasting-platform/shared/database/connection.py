"""
Database Connection Management
Async SQLAlchemy setup with connection pooling
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import create_engine, MetaData
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from shared.utils.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy Base for ORM models
Base = declarative_base()
metadata = MetaData()

# Naming convention for constraints (helps with migrations)
metadata.naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}


class Database:
    """Database connection manager (Singleton pattern)"""

    _engine = None
    _async_session_maker = None

    @classmethod
    async def connect(cls):
        """Initialize database connection pool"""
        if cls._engine is not None:
            logger.warning("Database already connected")
            return

        # Create async engine
        cls._engine = create_async_engine(
            settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
            echo=settings.ENVIRONMENT == "development",
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=True,  # Verify connections before using
            pool_recycle=3600,   # Recycle connections after 1 hour
        )

        # Create session factory
        cls._async_session_maker = async_sessionmaker(
            cls._engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )

        logger.info("Database connection pool initialized")

    @classmethod
    async def disconnect(cls):
        """Close database connection pool"""
        if cls._engine is None:
            logger.warning("Database not connected")
            return

        await cls._engine.dispose()
        cls._engine = None
        cls._async_session_maker = None

        logger.info("Database connection pool closed")

    @classmethod
    @asynccontextmanager
    async def session(cls) -> AsyncGenerator[AsyncSession, None]:
        """
        Get database session (async context manager)

        Usage:
            async with Database.session() as db:
                result = await db.execute(query)
        """
        if cls._async_session_maker is None:
            raise RuntimeError("Database not connected. Call Database.connect() first.")

        async with cls._async_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()

    @classmethod
    def get_engine(cls):
        """Get the database engine"""
        if cls._engine is None:
            raise RuntimeError("Database not connected")
        return cls._engine


# Dependency for FastAPI routes
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency for database sessions

    Usage in routes:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(Item))
            return result.scalars().all()
    """
    async with Database.session() as session:
        yield session


# Sync engine for migrations and admin tasks
def get_sync_engine():
    """Get synchronous engine for Alembic migrations"""
    return create_engine(
        settings.DATABASE_URL,
        echo=settings.ENVIRONMENT == "development",
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
    )
