"""Loads initial data on database."""
from typing import List, Any

from sqlalchemy.orm import Session

from goals.database.models import Metrics


def _insert(session, records: List[Any]) -> None:
    """Insert records."""
    for record in records:
        metric = session.query(Metrics).filter_by(name=record.name).first()
        if metric is not None:
            continue
        session.add(record)
    session.commit()


def insert_new_metrics(session: Session):
    """Prepare fixed metrics for loading in database."""
    new_metrics = [
        Metrics(name="distance", unit="km"),
        Metrics(name="muscle", unit="kg"),
        Metrics(name="fat", unit="kg"),
    ]
    _insert(session, new_metrics)


def initialize_db(session: Session) -> None:
    """Create basic data."""
    with session as open_session:
        insert_new_metrics(open_session)
