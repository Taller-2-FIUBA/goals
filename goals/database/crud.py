"""Handles CRUD database operations."""
from sqlalchemy.orm import Session
from goals.database.models import Goals, Metrics
from goals.schemas import GoalBase, GoalUpdate


def create_goal(session: Session, goal: GoalBase, user_id: str):
    """Create a new user in the users table, using the id as primary key."""
    new_goal = Goals(title=goal.title, description=goal.description,
                     metric=goal.metric, objective=goal.objective,
                     time_limit=goal.time_limit, user_id=user_id,
                     progress=0)
    session.add(new_goal)
    session.commit()
    session.refresh(new_goal)
    return new_goal.id


def get_user_goals(session: Session, user_id: str):
    """Return goals for user specified by user_id."""
    user_goals = []
    query = session.query(Goals, Metrics)
    q_filter = query.join(Goals).filter(Goals.metric == Metrics.name) \
        .filter(Goals.user_id == user_id)
    for goals, metrics in q_filter:
        user_goals.append({"id": goals.id,
                           "title": goals.title,
                           "description": goals.description,
                           "metric": metrics.name,
                           "objective": goals.objective,
                           "progress": goals.progress,
                           "unit": metrics.unit,
                           "time_limit": goals.time_limit})
    return user_goals


def get_goal(session: Session, goal_id: int):
    """Return details from a goal identified by a certain goal id."""
    return session.query(Goals).filter(Goals.id == goal_id).first()


def delete_goal(session: Session, goal_id: int):
    """Delete goal with specified goal ID."""
    session.query(Goals).filter(Goals.id == goal_id).delete()
    session.commit()


def update_goal(session: Session, goal_id: int, details: GoalUpdate):
    """Update goal with specified ID with provided data."""
    col = {
        col: val for col, val in details.__dict__.items() if val is not None
    }
    session.query(Goals).filter(Goals.id == goal_id).update(values=col)
    session.commit()


def get_all_metrics(session: Session):
    """Return all available metrics."""
    return session.query(Metrics).all()


def correct_user_id(session: Session, goal_id: int, _id: int):
    """Return all available metrics."""
    goal = session.query(Goals).filter(Goals.id == goal_id).first()
    if goal.user_id == _id:
        return True
    return False
