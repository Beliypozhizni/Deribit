from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Price
from src.domain.schemas.price import PriceFull


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


async def read_all_prices(session: AsyncSession, ticker: str) -> list[Price]:
    stmt = (
        select(Price)
        .where(Price.ticker == ticker)
        .order_by(Price.captured_ts_ms.desc())
    )
    return list(await session.scalars(stmt))


async def read_last_price(session: AsyncSession, ticker: str) -> Price | None:
    stmt = (
        select(Price)
        .where(Price.ticker == ticker)
        .order_by(Price.captured_ts_ms.desc())
        .limit(1)
    )
    result = await session.scalar(stmt)
    if result:
        return result
    raise HTTPException(status_code=404, detail="Price not found")


async def read_last_price_at_time(session: AsyncSession, ticker: str, ts: int) -> Price:
    stmt = (
        select(Price)
        .where(Price.ticker == ticker)
        .where(Price.captured_ts_ms <= ts)
        .order_by(Price.captured_ts_ms.desc())
        .limit(1)
    )
    result = await session.scalar(stmt)
    if result:
        return result
    raise HTTPException(status_code=404, detail="Price not found")
