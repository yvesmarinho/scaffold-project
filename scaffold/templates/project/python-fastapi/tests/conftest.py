from __future__ import annotations

import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.main import app


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    """Cliente HTTP assíncrono apontando para o app FastAPI em memória."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac
