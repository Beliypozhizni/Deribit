from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Price
from src.prices.schemas import PriceBase


async def create_price(session: AsyncSession, price_in: PriceBase) -> None:
    price = Price(**price_in.model_dump())
    session.add(price)
    await session.commit()
    await session.refresh(price)


async def create_prices(session: AsyncSession, prices_in: list[PriceBase]) -> None:
    if not prices_in:
        return

    values = [p.model_dump() for p in prices_in]

    stmt = insert(Price).values(values)

    stmt = stmt.on_conflict_do_nothing(index_elements=["ticker", "captured_ts_ms"])

    await session.execute(stmt)
    await session.commit()
