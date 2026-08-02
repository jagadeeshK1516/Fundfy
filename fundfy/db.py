"""Database engine, session factory, and initialization."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fundfy.config import settings

engine = create_async_engine(settings.database_url, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Create all tables."""
    from fundfy.models import Base

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Yield a database session."""
    async with async_session() as session:
        yield session
