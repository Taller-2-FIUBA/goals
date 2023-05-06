"""Defines table structure for each table in the database."""

from sqlalchemy import Column, ForeignKey, String, Integer
from sqlalchemy.orm import (
    Mapped, declarative_base, relationship, mapped_column
)

Base = declarative_base()


class UserGoals(Base):
    """Table structure for user goals."""

    __tablename__ = "user goals"
    user_id = Column(Integer, primary_key=True, autoincrement=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id"))

    # Relationships
    type: Mapped["Goals"] = relationship(lazy="joined")

    def __repr__(self):
        return f"<User goals {self.id}>"


class Goals(Base):
    """Table structure for goals."""

    __tablename__ = "goals"
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    description = Column(String)
    title = Column(String)
    metric = Column(String)
    objective = Column(Integer)
    time_limit = Column(String)

    def __repr__(self):
        return f"<Goal {self.id, self.title}>"