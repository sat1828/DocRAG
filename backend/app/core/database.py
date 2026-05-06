"""
Database configuration and session management.
Uses SQLAlchemy 2.0 with async support for PostgreSQL or SQLite.
Engine is created lazily to allow settings override in tests.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

# Lazy engine - created on first access
_engine = None
_session_factory = None

def get_engine():
    """Get or create the async engine (lazy initialization)."""
    global _engine
    if _engine is None:
        db_url = settings.DATABASE_URL
        
        # Fix SQLite URL for async
        if "sqlite" in db_url and not db_url.startswith("sqlite+aiosqlite"):
            db_url = db_url.replace("sqlite://", "sqlite+aiosqlite://")
        
        if "sqlite" in db_url:
            _engine = create_async_engine(
                db_url,
                echo=settings.ENVIRONMENT == "development",
                connect_args={"check_same_thread": False},
            )
        else:
            _engine = create_async_engine(
                settings.DATABASE_URL,
                echo=settings.ENVIRONMENT == "development",
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
            )
    return _engine


def get_session_factory():
    """Get or create the session factory."""
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _session_factory


def reset_engine():
    """Reset the engine (for testing)."""
    global _engine, _session_factory
    _engine = None
    _session_factory = None


# Base class for all SQLAlchemy models
class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncSession:
    """Dependency that provides an async database session."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables (for development/testing)."""
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db():
    """Close database engine."""
    engine = get_engine()
    await engine.dispose()
    reset_engine()
