from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import urljoin

import aiohttp

from .config import (
    DERIBIT_BASE_URL,
    ERROR_KEY,
    INDEX_PRICE_ENDPOINT,
    INDEX_PRICE_KEY,
    RESULT_KEY,
)
from src.prices.schemas import PriceBase


class DeribitError(Exception):
    """Base error for Deribit integration."""


class UnsupportedTicker(DeribitError):
    """Ticker is not supported by this service/client."""


class DeribitUnavailable(DeribitError):
    """Network issues, timeouts, or transient server failures (5xx)."""


class DeribitRateLimited(DeribitError):
    """Deribit rate limiting (429)."""


class DeribitBadResponse(DeribitError):
    """Unexpected response format / missing keys / invalid data."""


@dataclass(frozen=True, slots=True)
class DeribitClientConfig:
    base_url: str = DERIBIT_BASE_URL
    endpoint: str = INDEX_PRICE_ENDPOINT
    timeout_s: float = 10.0
    concurrency: int = 10


class DeribitClient:
    """
    Deribit HTTP client (aiohttp).
    """

    _TICKER_TO_INDEX_NAME: dict[str, str] = {
        "btc_usd": "btc_usd",
        "eth_usd": "eth_usd",
    }

    def __init__(
        self,
        config: DeribitClientConfig | None = None,
        session: aiohttp.ClientSession | None = None,
    ) -> None:
        self._config = config or DeribitClientConfig()
        self._session: aiohttp.ClientSession | None = session
        self._owns_session = session is None
        self._semaphore = asyncio.Semaphore(self._config.concurrency)

    async def __aenter__(self) -> "DeribitClient":
        if self._session is None:
            self._session = self._create_session()
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    def _create_session(self) -> aiohttp.ClientSession:
        timeout = aiohttp.ClientTimeout(total=self._config.timeout_s)
        return aiohttp.ClientSession(timeout=timeout)

    async def aclose(self) -> None:
        if (
            self._owns_session
            and self._session is not None
            and not self._session.closed
        ):
            await self._session.close()
        self._session = None

    def _normalize_ticker(self, ticker: str) -> str:
        t = ticker.strip().lower()
        if t not in self._TICKER_TO_INDEX_NAME:
            raise UnsupportedTicker(f"Unsupported ticker: {ticker!r}")
        return t

    def _build_url(self) -> str:
        return urljoin(
            self._config.base_url.rstrip("/") + "/", self._config.endpoint.lstrip("/")
        )

    async def get_index_price(self, ticker: str) -> PriceBase:
        """
        Fetch index price for a single ticker.
        """
        if self._session is None:
            self._session = self._create_session()
            self._owns_session = True

        normalized = self._normalize_ticker(ticker)
        index_name = self._TICKER_TO_INDEX_NAME[normalized]
        url = self._build_url()

        async with self._semaphore:
            try:
                async with self._session.get(
                    url, params={"index_name": index_name}
                ) as resp:
                    status = resp.status

                    if status == 429:
                        raise DeribitRateLimited("Deribit rate limited (HTTP 429)")
                    if 500 <= status <= 599:
                        raise DeribitUnavailable(
                            f"Deribit server error (HTTP {status})"
                        )
                    if status >= 400:
                        text = await resp.text()
                        raise DeribitBadResponse(f"Deribit HTTP {status}: {text[:200]}")

                    data = await resp.json()

            except (
                aiohttp.ClientConnectionError,
                aiohttp.ClientPayloadError,
                asyncio.TimeoutError,
            ) as e:
                raise DeribitUnavailable(f"Deribit request failed: {e!r}") from e
            except aiohttp.ContentTypeError as e:
                raise DeribitBadResponse(
                    f"Expected JSON response, got invalid content-type: {e!r}"
                ) from e

        if isinstance(data, dict) and data.get(ERROR_KEY):
            raise DeribitBadResponse(
                f"Deribit returned error payload: {data.get(ERROR_KEY)!r}"
            )

        try:
            result = data[RESULT_KEY]
            price_raw = result[INDEX_PRICE_KEY]
        except Exception as e:
            raise DeribitBadResponse(f"Missing expected keys in response: {e!r}") from e

        try:
            price = float(price_raw)
        except (TypeError, ValueError) as e:
            raise DeribitBadResponse(f"Invalid price value: {price_raw!r}") from e

        captured_ts_ms = int(time.time() * 1000)

        return PriceBase(
            ticker=normalized,
            price=price,
            captured_ts_ms=captured_ts_ms,
        )

    async def get_index_prices(self, tickers: Iterable[str]) -> list[PriceBase]:
        """
        Fetch index price for multiple tickers.
        """
        ticker_list = list(tickers)
        tasks = [self.get_index_price(t) for t in ticker_list]
        return await asyncio.gather(*tasks)
