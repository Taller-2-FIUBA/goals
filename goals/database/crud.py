"""Handles CRUD database operations."""
from sqlalchemy import desc
from sqlalchemy.orm import Session
from goals.database.models import Goals, Metrics, MetricsRecords
from goals.database.util import current_date
from goals.schemas import GoalBase, GoalUpdate


def create_goal(session: Session, goal: GoalBase, user_id: int):
    """Create a new user in the goals table, using the id as primary key."""
    new_goal = Goals(title=goal.title, description=goal.description,
                     metric=goal.metric, objective=goal.objective,
                     time_limit=goal.time_limit, user_id=user_id,
                     progress=0)
    session.add(new_goal)
    session.commit()
    session.refresh(new_goal)
    return new_goal.id


def get_user_goals(session: Session, user_id: int):
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


def get_general_progress(session, metric, user_id, days):
    """Get a metric's progress in the specified amount of time."""
    date = current_date()
    metric_exists = session.query(Metrics).\
        filter(Metrics.name == metric).first()
    if metric_exists is None:
        return None
    records = session.query(MetricsRecords).\
        filter(MetricsRecords.user_id == user_id) \
        .filter(MetricsRecords.metric_name == metric) \
        .order_by(desc(MetricsRecords.date)).all()
    if records is None or len(records) == 0:
        return 0
    latest_progress = 0
    oldest_progress = 0
    for record in records:
        delta = (date - record.date).days
        if delta <= days and latest_progress == 0:
            latest_progress = record.value
        if delta > days and oldest_progress == 0:
            oldest_progress = record.value
    if latest_progress > 0:
        return latest_progress - oldest_progress
    return 0


def update_goal(session: Session, goal_id: int, details: GoalUpdate):
    """Update goal with specified ID with provided data."""
    initial_goal = get_goal(session, goal_id)
    progress_delta = details.progress - initial_goal.progress
    col = {
        col: val for col, val in details.__dict__.items() if val is not None
    }
    session.query(Goals).filter(Goals.id == goal_id).update(values=col)
    session.commit()
    return progress_delta


def get_latest_record(session, metric_name, user_id):
    """Get latest metric record for a certain user_id."""
    return session.query(MetricsRecords).\
        filter(MetricsRecords.user_id == user_id) \
        .filter(MetricsRecords.metric_name == metric_name)\
        .order_by(desc(MetricsRecords.date)).first()


def new_metric_record(session: Session, goal_id: int, progress_delta: int):
    """Create new metric record after a progress update."""
    goal = session.query(Goals).filter(Goals.id == goal_id).first()
    latest_record = get_latest_record(session, goal.metric, goal.user_id)
    new_value = goal.progress
    if latest_record is not None:
        new_value = latest_record.value + progress_delta
    new_record = MetricsRecords(metric_name=goal.metric, user_id=goal.user_id,
                                value=new_value, date=current_date())
    session.add(new_record)
    session.commit()
    session.refresh(new_record)


def get_all_metrics(session: Session):
    """Return all available metrics."""
    return session.query(Metrics).all()


def correct_user_id(session: Session, goal_id: int, _id: int):
    """Return all available metrics."""
    goal = session.query(Goals).filter(Goals.id == goal_id).first()
    if goal.user_id == _id:
        return True
    return False
