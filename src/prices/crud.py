from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.enums import Ticker
from src.domain.schemas.price import PriceFull
from src.models import Price


async def create_price(session: AsyncSession, price_in: PriceFull) -> Price:
    price = Price(**price_in.model_dump())
    session.add(price)
    await session.commit()
    await session.refresh(price)
    return price


async def create_prices(
    session: AsyncSession, prices_in: list[PriceFull]
) -> list[Price]:
    values = [p.model_dump() for p in prices_in]
    stmt = (
        insert(Price)
        .values(values)
        .on_conflict_do_nothing(index_elements=["ticker", "captured_ts_ms"])
        .returning(Price)
    )
    result = await session.scalars(stmt)
    models = list(result)
    await session.commit()
    return models


async def read_all_prices(session: AsyncSession, ticker: Ticker) -> list[Price]:
    stmt = (
        select(Price)
        .where(Price.ticker == ticker.value)
        .order_by(Price.captured_ts_ms.desc())
    )
    return list(await session.scalars(stmt))


async def read_last_price(session: AsyncSession, ticker: Ticker) -> Price | None:
    stmt = (
        select(Price)
        .where(Price.ticker == ticker.value)
        .order_by(Price.captured_ts_ms.desc())
        .limit(1)
    )
    return await session.scalar(stmt)


async def read_last_price_at_time(
    session: AsyncSession,
    ticker: Ticker,
    ts: int,
) -> Price | None:
    stmt = (
        select(Price)
        .where(Price.ticker == ticker.value)
        .where(Price.captured_ts_ms <= ts)
        .order_by(Price.captured_ts_ms.desc())
        .limit(1)
    )
    return await session.scalar(stmt)
