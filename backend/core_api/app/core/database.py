# DB Configuration, Session Management, SQLAlchemy

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import func
from app.core.config import settings


class Base(DeclarativeBase):
    ...


engine = create_async_engine(
    str(settings.DATABASE_URL),
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

async_session_maker = async_sessionmaker(engine,class_=AsyncSession,expire_on_commit=False,autoflush=False,)


async def get_db() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()

async def init_db() -> None:
    # Initialize DB & Create Tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def check_db(db: AsyncSession) -> None:
    #Force a real server round-trip; raises on failure.
    # Used by /health/db so liveness never depends on pool_pre_ping.
    # Constant expression — no external input involved.
    

    await db.scalar(func.now())