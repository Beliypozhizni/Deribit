from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.enums import Ticker
from src.domain.schemas.price import PriceRead
from src.models import db_helper
from src.prices import crud

router = APIRouter(tags=["Prices"])


@router.get("/all", response_model=list[PriceRead], status_code=200)
async def get_ticker_prices(
    ticker: Ticker,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    return await crud.read_all_prices(session, ticker)


@router.get("/last", response_model=PriceRead, status_code=200)
async def get_ticker_last_price(
    ticker: Ticker,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    model = await crud.read_last_price(session, ticker)
    if model is None:
        raise HTTPException(status_code=404, detail="Price not found")
    return model


@router.get("/lastAtTime", response_model=PriceRead, status_code=200)
async def get_last_price_at_ts(
    ticker: Ticker,
    ts: int,
    session: AsyncSession = Depends(db_helper.session_dependency),
):
    model = await crud.read_last_price_at_time(session, ticker, ts)
    if model is None:
        raise HTTPException(status_code=404, detail="Price not found")
    return model
