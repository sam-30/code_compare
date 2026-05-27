"""
Test configuration.

Table creation/teardown is done synchronously via psycopg2 once per session
so we avoid asyncpg event-loop-scoping pitfalls. Each test then gets its own
fresh NullPool async engine for the actual async work.
"""
import os
import pytest
import pytest_asyncio
import psycopg2
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.models as _models  # noqa: F401 — registers all ORM models with Base.metadata
from app.core.database import Base, get_db
from app.core.security import get_current_user
from app.main import app

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://codecmp:codecmp@localhost:5433/codecmp_test",
)

# Sync URL for psycopg2 (same host/db, different driver prefix)
TEST_DATABASE_URL_SYNC = TEST_DATABASE_URL.replace(
    "postgresql+asyncpg://", "postgresql://"
)


def make_engine():
    return create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)


@pytest.fixture(scope="session", autouse=True)
def create_test_tables():
    """Create all tables synchronously once before the test session."""
    from sqlalchemy import create_engine
    sync_engine = create_engine(TEST_DATABASE_URL_SYNC)
    Base.metadata.create_all(sync_engine)
    sync_engine.dispose()
    yield
    sync_engine = create_engine(TEST_DATABASE_URL_SYNC)
    Base.metadata.drop_all(sync_engine)
    sync_engine.dispose()


@pytest_asyncio.fixture
async def db_session(create_test_tables) -> AsyncSession:
    engine = make_engine()
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


_test_user_counter = 0


@pytest_asyncio.fixture
async def test_user(db_session: AsyncSession):
    global _test_user_counter
    _test_user_counter += 1
    from app.models.user import User
    user = User(email=f"test_user_{_test_user_counter}@example.com", hashed_password="fake_hash")
    db_session.add(user)
    await db_session.flush()
    return user


@pytest_asyncio.fixture
async def client(db_session: AsyncSession, test_user) -> AsyncClient:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = lambda: test_user
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
