import asyncio
import tempfile
import uuid
from typing import AsyncGenerator
from pathlib import Path
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import StaticPool

from app.api.dependencies import get_db
from app.core.config import settings
from app.core.security import create_access_token
from app.main import app
from app.models.base import Base

# In-memory SQLite for testing
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest_asyncio.fixture(scope="session")
def event_loop():
    """Default event loop for tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db(tmp_path: Path):
    """Sets up database tables and a clean temporary storage path for each test."""
    # Point settings to temp storage dir
    temp_storage = tmp_path / "tickets"
    temp_storage.mkdir(parents=True, exist_ok=True)
    orig_storage = settings.STORAGE_PATH
    settings.STORAGE_PATH = str(temp_storage)

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    settings.STORAGE_PATH = orig_storage


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a transactional database session for tests."""
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client configured with test session dependency override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def internal_headers():
    return {"X-Internal-Token": settings.INTERNAL_TOKEN}


@pytest.fixture
def client_jwt_headers():
    token = create_access_token(
        {
            "sub": str(uuid.uuid4()),
            "name": "Juan Perez",
            "email": "cliente@entradasya.com",
            "role": "cliente",
        }
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def portero_jwt_headers():
    token = create_access_token(
        {
            "sub": str(uuid.uuid4()),
            "name": "Portero Uno",
            "email": "portero@entradasya.com",
            "role": "portero",
        }
    )
    return {"Authorization": f"Bearer {token}"}
