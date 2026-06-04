from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import NullPool, text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.database import Base, get_db
from app.core.redis import get_redis
from app.core.security import hash_password
from app.main import create_app
from app.models.users import User


TEST_DB_URL = "postgresql+asyncpg://postgres:corehub@localhost:5432/corehub_test"

test_engine = create_async_engine(
    TEST_DB_URL,
    echo=True,
    poolclass=NullPool,
)

TestAsyncSession = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope='session', autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await test_engine.dispose()

@pytest_asyncio.fixture
async def db_session():
    async with TestAsyncSession() as session:
        await session.execute(text("""
            TRUNCATE
                refresh_tokens,
                messages,
                conversation_members,
                conversations,
                notifications,
                tasks,
                announcements,
                departments,
                users
            CASCADE
        """))
        await session.commit()

        yield session

        await session.close()

@pytest.fixture
def mock_redis():
    redis = AsyncMock()
    redis.get.return_value = None
    redis.set.return_value = True
    redis.delete.return_value = True
    redis.scan_iter.return_value = AsyncMock()
    return redis

@pytest_asyncio.fixture
async def client(db_session, mock_redis):
    app = create_app()

    async def override_get_db():
        yield db_session

    async def override_get_redis():
        yield mock_redis

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.clear()



@pytest_asyncio.fixture
async def admin_user(db_session):
    user = User(
        first_name="Admin",
        last_name="User",
        username="admin_test",
        email="admin@test.com",
        hashed_password=hash_password("adminadmin"),
        role="admin",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def manager_user(db_session):
    user = User(
        first_name="Manager",
        last_name="User",
        username="manager_test",
        email="manager@test.com",
        hashed_password=hash_password("managermanager"),
        role="manager",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user

@pytest_asyncio.fixture
async def employee_user(db_session):
    user = User(
        first_name="Employee",
        last_name="User",
        username="employee_test",
        email="employee@test.com",
        hashed_password=hash_password("employee"),
        role="employee",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


async def get_auth_headers(
    client: AsyncClient,
    username: str,
    password: str,
) -> dict[str, str]:
    response = await client.post(
        "/auth/login",
        data={
            "username": username,
            "password": password,
        },
    )

    assert response.status_code == 200
    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}