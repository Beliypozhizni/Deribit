import pytest

from src.domain.enums import Ticker
from src.domain.schemas.price import PriceFull
from src.prices.crud import create_prices

pytestmark = pytest.mark.anyio


async def _seed_prices(session):
    prices = [
        PriceFull(
            ticker=Ticker.BTC_USD,
            price=50000,
            captured_ts_ms=1000,
        ),
        PriceFull(
            ticker=Ticker.BTC_USD,
            price=51000,
            captured_ts_ms=2000,
        ),
        PriceFull(
            ticker=Ticker.ETH_USD,
            price=2000,
            captured_ts_ms=1500,
        ),
    ]

    await create_prices(session, prices)


async def test_get_all_prices(client, db_session):
    await _seed_prices(db_session)

    resp = await client.get(
        "/api/v1/prices/all",
        params={"ticker": Ticker.BTC_USD.value},
    )

    assert resp.status_code == 200

    data = resp.json()

    assert len(data) == 2

    assert data[0]["captured_ts_ms"] > data[1]["captured_ts_ms"]


async def test_get_all_prices_empty(client):
    resp = await client.get(
        "/api/v1/prices/all",
        params={"ticker": Ticker.BTC_USD.value},
    )

    assert resp.status_code == 200
    assert resp.json() == []


async def test_get_last_price(client, db_session):
    await _seed_prices(db_session)

    resp = await client.get(
        "/api/v1/prices/last",
        params={"ticker": Ticker.BTC_USD.value},
    )

    assert resp.status_code == 200

    data = resp.json()

    assert data["price"] == 51000
    assert data["captured_ts_ms"] == 2000


async def test_get_last_price_not_found(client):
    resp = await client.get(
        "/api/v1/prices/last",
        params={"ticker": Ticker.BTC_USD.value},
    )

    assert resp.status_code == 404
    assert resp.json()["detail"] == "Price not found"


async def test_get_last_price_at_time(client, db_session):
    await _seed_prices(db_session)

    resp = await client.get(
        "/api/v1/prices/lastAtTime",
        params={
            "ticker": Ticker.BTC_USD.value,
            "ts": 1500,
        },
    )

    assert resp.status_code == 200

    data = resp.json()

    assert data["captured_ts_ms"] == 1000


async def test_get_last_price_at_time_not_found(client):
    resp = await client.get(
        "/api/v1/prices/lastAtTime",
        params={
            "ticker": Ticker.BTC_USD.value,
            "ts": 1000,
        },
    )

    assert resp.status_code == 404
