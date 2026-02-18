from dataclasses import dataclass


@dataclass(frozen=True)
class BookLevel:
    price: float
    size: float


@dataclass(frozen=True)
class BookSnapshot:
    token_id: str
    sequence: int
    bids: tuple[BookLevel, ...]
    asks: tuple[BookLevel, ...]
