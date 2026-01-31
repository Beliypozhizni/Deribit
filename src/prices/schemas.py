from pydantic import BaseModel


class PriceBase(BaseModel):
    ticker: str
    price: float
    captured_ts_ms: int
