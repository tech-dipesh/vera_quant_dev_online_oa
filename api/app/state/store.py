from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.models import Fill, Position, Side
from app.state.models import Base, FillRecord, PositionSnapshotRecord


class StateStore:
    def __init__(self, database_url: str) -> None:
        self._engine = create_engine(database_url)
        Base.metadata.create_all(self._engine)

    def record_fill(self, symbol: str, fill: Fill) -> None:
        with Session(self._engine) as session:
            session.add(
                FillRecord(
                    symbol=symbol,
                    side=fill.side.value,
                    price=fill.price,
                    quantity=fill.quantity,
                    timestamp=fill.timestamp,
                )
            )
            session.commit()

    def fill_count(self, symbol: str) -> int:
        with Session(self._engine) as session:
            return session.query(FillRecord).filter_by(symbol=symbol).count()

    def save_position_snapshot(self, position: Position) -> None:
        with Session(self._engine) as session:
            record = session.get(PositionSnapshotRecord, position.symbol)
            if record is None:
                record = PositionSnapshotRecord(
                    symbol=position.symbol, quantity=0, average_price=0.0, realized_pnl=0.0
                )
                session.add(record)
            record.side = position.side.value if position.side else None
            record.quantity = position.quantity
            record.average_price = position.average_price
            record.realized_pnl = position.realized_pnl
            session.commit()

    def load_position(self, symbol: str) -> Position | None:
        with Session(self._engine) as session:
            record = session.get(PositionSnapshotRecord, symbol)
            if record is None:
                return None
            return Position(
                symbol=symbol,
                side=Side(record.side) if record.side else None,
                quantity=record.quantity,
                average_price=record.average_price,
                realized_pnl=record.realized_pnl,
            )

    def drop_all(self) -> None:
        Base.metadata.drop_all(self._engine)

    def close(self) -> None:
        self._engine.dispose()
