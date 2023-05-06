"""Handles CRUD database operations."""
from sqlalchemy.orm import Session
from goals.database.models import Goals
from goals.schemas import GoalBase


def create_goal(session: Session, goal: GoalBase):
    """Create a new user in the users table, using the id as primary key."""
    new_goal = Goals(title=goal.title, description=goal.description,
                     metric=goal.metric, objective=goal.objective,
                     time_limit=goal.time_limit)
    session.add(new_goal)
    session.commit()
    session.refresh(new_goal)
    return new_goal


def get_all_goals(session: Session):
    """Return all users currently present in the session."""
    return session.query(Goals).all()
