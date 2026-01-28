from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from celery.utils.log import get_task_logger

from src.deribit.client import (
    DeribitClient,
    DeribitRateLimited,
    DeribitUnavailable,
)

logger = get_task_logger(__name__)

TICKERS = ("btc_usd", "eth_usd")


async def _collect_prices_async() -> list[dict]:
    async with DeribitClient() as client:
        dtos = await client.get_index_prices(TICKERS)

    return [
        {
            "ticker": dto.ticker,
            "price": dto.price,
            "captured_ts_ms": dto.captured_ts_ms,
        }
        for dto in dtos
    ]


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_transient_exc(exc: Exception) -> bool:
    return isinstance(exc, (DeribitUnavailable, DeribitRateLimited))


from .celery_app import celery_app


@celery_app.task(
    name="src.worker.tasks.collect_prices",
    bind=True,
    autoretry_for=(DeribitUnavailable, DeribitRateLimited),
    retry_backoff=True,
    retry_backoff_max=60,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def collect_prices(self) -> list[dict]:
    logger.info("Collecting prices at %s", _utc_now_iso())

    try:
        result = asyncio.run(_collect_prices_async())
    except Exception as exc:
        if _is_transient_exc(exc):
            raise
        logger.exception("Non-retryable error while collecting prices: %r", exc)
        raise

    for item in result:
        logger.info(
            "PRICE %s = %s (captured_ts_ms=%s)",
            item["ticker"],
            item["price"],
            item["captured_ts_ms"],
        )

    return result
