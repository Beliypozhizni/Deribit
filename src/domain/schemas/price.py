from pydantic import BaseModel

from src.domain.enums import Ticker


class PriceRead(BaseModel):
    price: float
    captured_ts_ms: int


class PriceFull(PriceRead):
    ticker: Ticker
