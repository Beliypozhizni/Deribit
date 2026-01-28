from pydantic import BaseModel


class PriceDTO(BaseModel):
    ticker: str
    price: float
    captured_ts_ms: int
