"""Database engine, session factory, and initialization."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from fundfy.config import settings

_engine_kwargs = {}
if settings.database_url.startswith("postgresql"):
    _engine_kwargs = {
        "pool_size": 20,
        "max_overflow": 10,
    }

engine = create_async_engine(settings.database_url, echo=False, **_engine_kwargs)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    """Create all tables (used in dev/test mode; production uses Alembic)."""
    from fundfy.config import settings as _settings

    if _settings.environment in ("development", "test"):
        from fundfy.models import Base
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


async def get_session():
    """Yield a database session."""
    async with async_session() as session:
        yield session
