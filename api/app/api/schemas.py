from pydantic import BaseModel


class PositionOut(BaseModel):
    symbol: str
    side: str | None
    quantity: int
    average_price: float
    realized_pnl: float


class DemoStatusOut(BaseModel):
    running: bool
    symbol: str
    engines: list[str]


class FlattenResultOut(BaseModel):
    closed: int
