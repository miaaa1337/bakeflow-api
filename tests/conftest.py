import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

import database
from database import Base, get_db
from main import app

TEST_DATABASE_URL = (
    "postgresql+asyncpg://postgres:my_secret_pass_123@localhost:5432/cookie_flow_test"
)

engine_test = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = async_sessionmaker(
    engine_test, class_=AsyncSession, expire_on_commit=False
)


async def override_get_db():
  async with TestingSessionLocal() as session:
    yield session


@pytest_asyncio.fixture(autouse=True, scope="session")
async def setup_test_db():
  app.dependency_overrides[get_db] = override_get_db
  app.dependency_overrides[database.get_db] = override_get_db
  async with engine_test.begin() as conn:
    await conn.run_sync(Base.metadata.drop_all)
    await conn.run_sync(Base.metadata.create_all)
  yield
  async with engine_test.begin() as conn:
    await conn.run_sync(Base.metadata.drop_all)
  app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="session")
async def ac(setup_test_db):  
  transport = ASGITransport(app=app)
  async with AsyncClient(transport=transport, base_url="http://test") as client:
    yield client




@pytest_asyncio.fixture(autouse=True)
async def clean_tables():
  # Очищаем данные ПЕРЕД каждым тестом, чтобы каждый тест начинал с чистой БД
  async with TestingSessionLocal() as session:
    await session.execute(
        text(
            "TRUNCATE TABLE cookies, orders, order_items RESTART IDENTITY"
            " CASCADE;"
        )
    )
    await session.commit()
  yield


@pytest_asyncio.fixture
async def employee_ac(authenticated_ac):
  # 1. Менеджер регистрирует пекаря через API (запись точно попадает в базу FastAPI)
  reg_data = {
      "employee_id": 67,
      "name": "Test Baker",
      "pin_code": "1388",
      "role": "baker",
      "is_active": True,
  }
  await authenticated_ac.post("/register", json=reg_data)

  transport = ASGITransport(app=app)
  async with AsyncClient(
      transport=transport, base_url="http://test"
  ) as client:
    login_resp = await client.post(
        "/login", json={"employee_id": 67, "pin_code": "1388"}
    )
    token = login_resp.json()["access_token"]

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as baker_client:
      yield baker_client


@pytest_asyncio.fixture
async def authenticated_ac(clean_tables, ac):
  async with TestingSessionLocal() as session:
    import models
    from auth import hash_pin

    stmt = select(models.UserModel).where(models.UserModel.employee_id == 54)
    result = await session.execute(stmt)
    user = result.scalars().first()

    if not user:
      test_employee = models.UserModel(
          employee_id=54,
          name="Test Manager",
          pin_code_hash=hash_pin("1337"),
          role="manager",
          is_active=True,
      )
      session.add(test_employee)
      await session.commit()

  login_data = {"employee_id": 54, "pin_code": "1337"}
  response = await ac.post("/login", json=login_data)
  token = response.json()["access_token"]
  transport = ASGITransport(app=app)
  async with AsyncClient(
    transport=transport,
    base_url="http://test",
    headers={"Authorization": f"Bearer {token}"},  # Заголовок только у этого клиента!
  ) as auth_client:
    yield auth_client


@pytest_asyncio.fixture
async def emp_inv_ac(authenticated_ac, ac):
  # 1. Менеджер регистрирует неактивного пекаря через API
  reg_data = {
      "employee_id": 57,
      "name": "No Baker",
      "pin_code": "3434",
      "role": "baker",
      "is_active": False,
  }
  await authenticated_ac.post("/register", json=reg_data)

  # 2. Возвращаем неавторизованный клиент для попытки логина
  yield ac