from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.core.config import settings

# Supabase PostgreSQL requires connecting via asyncpg for async support.
# Create the async engine. We disable echo in production for performance.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    # Pool settings are important for serverless DBs like Supabase
    pool_size=5,
    max_overflow=10,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db():
    """
    Dependency to provide a database session to endpoints.
    Ensures the session is closed after the request is finished.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
