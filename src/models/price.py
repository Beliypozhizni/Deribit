from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Numeric,
    String,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.models.base import Base


class Price(Base):
    ticker: Mapped[str] = mapped_column(String(32), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(20, 10), nullable=False)
    captured_ts_ms: Mapped[int] = mapped_column(BigInteger, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "ticker", "captured_ts_ms", name="uq_prices_ticker_captured_ts_ms"
        ),
        Index("ix_prices_ticker_captured_ts_ms", "ticker", "captured_ts_ms"),
        Index("ix_prices_captured_ts_ms", "captured_ts_ms"),
    )
