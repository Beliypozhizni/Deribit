from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from celery.utils.log import get_task_logger

from src.deribit.client import (
    DeribitClient,
    DeribitRateLimited,
    DeribitUnavailable,
)
from src.prices.crud import create_prices
from ..models.db_helper import db_helper
from ..prices.schemas import PriceBase

logger = get_task_logger(__name__)

event_loop = asyncio.new_event_loop()
asyncio.set_event_loop(event_loop)

TICKERS = ("btc_usd", "eth_usd")


async def _collect_prices_async() -> list[PriceBase]:
    async with DeribitClient() as client:
        prices = await client.get_index_prices(TICKERS)

    return prices


async def _save_prices(prices: list[PriceBase]) -> None:
    async with db_helper.session_factory() as session:
        await create_prices(session=session, prices_in=prices)


async def _collect_and_save_prices_async():
    prices = await _collect_prices_async()
    await _save_prices(prices)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_transient_exc(exc: Exception) -> bool:
    return isinstance(exc, (DeribitUnavailable, DeribitRateLimited))


from .celery_app import celery_app


@celery_app.task(
    name="src.worker.tasks.collect_and_save_prices",
    bind=True,
    autoretry_for=(DeribitUnavailable, DeribitRateLimited),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def collect_and_save_prices(self):
    logger.info("Collecting and saving prices at %s", _utc_now_iso())

    try:
        event_loop.run_until_complete(_collect_and_save_prices_async())
    except Exception as exc:
        if _is_transient_exc(exc):
            raise
        logger.exception(
            "Non-retryable error while collecting and saving prices: %r", exc
        )
        raise
