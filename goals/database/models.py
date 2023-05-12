"""Defines table structure for each table in the database."""

from sqlalchemy import Column, ForeignKey, String, Integer
from sqlalchemy.orm import (
    Mapped, declarative_base, mapped_column
)

Base = declarative_base()


class Goals(Base):
    """Table structure for goals."""

    __tablename__ = "goals"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    description = Column(String)
    title = Column(String)
    metric = Column(String, ForeignKey("metrics.name"), nullable=False)
    objective = Column(Integer)
    time_limit = Column(String)
    progress = Column(Integer)

    def __repr__(self):
        return f"<Goal {self.id, self.title}>"


class Metrics(Base):
    """Table structure for all pre-determined metrics."""

    __tablename__ = "metrics"
    name = Column(String, primary_key=True, autoincrement=False)
    unit = Column(String)

    def __repr__(self):
        return f"<Metric {self.name, self.unit}>"
