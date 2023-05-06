# pylint: disable=no-name-in-module
"""Defines models for data exchange in API and between modules."""
from pydantic import BaseModel


class GoalBase(BaseModel):
    """Goal creation DTO."""

    title: str
    description: str
    metric: str
    objective: int
    time_limit: str


class Goal(GoalBase):
    """Goal DTO for database."""

    id: int

    class Config:
        """Required to enable orm."""

        orm_mode = True
