from pydantic import BaseModel

from src.domain.enums import Ticker


class TickerBase(BaseModel):
    ticker: Ticker
