import asyncio
import os
import subprocess
from typing import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.main import app
from src.models import db_helper


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


def _assert_test_db() -> None:
    url = str(db_helper.engine.url).lower()
    if "test" not in url:
        raise RuntimeError(f"Refusing to run tests on non-test DB: {url}")


async def _run_subprocess(cmd: list[str]) -> None:
    await asyncio.to_thread(subprocess.run, cmd, check=True)


@pytest.fixture(scope="session", autouse=True)
async def prepare_database():
    if os.getenv("ENV_FILE") != ".env.test":
        raise RuntimeError(
            "Set ENV_FILE=.env.test before running tests.\n"
            "Example:\n"
            "  $env:ENV_FILE = '.env.test'\n"
            "  pytest"
        )

    _assert_test_db()

    async with db_helper.engine.begin() as conn:
        await conn.execute(text("DROP SCHEMA public CASCADE;"))
        await conn.execute(text("CREATE SCHEMA public;"))

    await _run_subprocess(["alembic", "upgrade", "head"])

    yield

    await db_helper.engine.dispose()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    async with db_helper.session_factory() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession):
    async def _override_session_dependency():
        yield db_session

    app.dependency_overrides[db_helper.session_dependency] = (
        _override_session_dependency
    )

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as client:
        yield client

    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
async def truncate_tables(db_session):
    await db_session.execute(text("TRUNCATE prices RESTART IDENTITY CASCADE;"))
    await db_session.commit()
