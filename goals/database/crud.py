"""Handles CRUD database operations."""
from sqlalchemy.orm import Session
from goals.database.models import Goals, UserGoals
from goals.schemas import GoalBase


def create_goal(session: Session, goal: GoalBase):
    """Create a new user in the users table, using the id as primary key."""
    new_goal = Goals(title=goal.title, description=goal.description,
                     metric=goal.metric, objective=goal.objective,
                     unit=goal.unit, time_limit=goal.time_limit)
    session.add(new_goal)
    session.commit()
    session.refresh(new_goal)
    return new_goal.id


def get_user_goals(session: Session, user_id: str):
    """Return all users currently present in the session."""
    user_goals = []
    query = session.query(Goals, UserGoals).filter(UserGoals.user_id
                                                   == user_id).all()
    for goals, u_goals in query:
        user_goals.append({"id": goals.id,
                           "title": goals.title,
                           "description": goals.description,
                           "metric": goals.metric,
                           "objective": goals.objective,
                           "value": u_goals.value,
                           "unit": goals.unit,
                           "time_limit": goals.time_limit})
    return user_goals


def get_goal_by_id(session: Session, goal_id: int):
    """Return details from a goal identified by a certain goal id."""
    return session.query(Goals).filter(Goals.id == goal_id).first()


def add_goal(session: Session, user_id: str, goal_id: int):
    """Add goal in UserGoals table with starting value 0."""
    new_goal = UserGoals(user_id=user_id, goal_id=goal_id, value=0)
    session.add(new_goal)
    session.commit()
    session.refresh(new_goal)
