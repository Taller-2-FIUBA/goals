"""Requests handlers."""
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import JSONResponse
from environ import to_config
from prometheus_client import start_http_server, Counter
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from goals.config import AppConfig
from goals.database.crud import create_goal, get_user_goals, get_goal, \
    get_all_metrics, delete_goal, update_goal
from goals.database.models import Base
from goals.database.initialization import get_database_url
from goals.schemas import GoalBase, GoalUpdate

BASE_URI = "/goals"

REQUEST_COUNTER = Counter(
    "my_failures", "Description of counter", ["endpoint", "http_verb"]
)

CONFIGURATION = to_config(AppConfig)
start_http_server(CONFIGURATION.prometheus_port)
app = FastAPI()

ENGINE = create_engine(get_database_url(CONFIGURATION))
if CONFIGURATION.db.create_structures:
    Base.metadata.create_all(bind=ENGINE)


def get_db() -> Session:
    """Create a session."""
    return Session(autocommit=False, autoflush=False, bind=ENGINE)


@app.post(BASE_URI + "/{user_id}")
async def add_goal_for_user(goal: GoalBase, user_id: str,
                            session: Session = Depends(get_db)):
    """Create a new goal for user_id."""
    with session as open_session:
        _id = create_goal(session=open_session, goal=goal, user_id=user_id)
        return _id


@app.get(BASE_URI + "/metrics")
async def get_metrics(session: Session = Depends(get_db)):
    """Return all metrics in database."""
    with session as open_session:
        return get_all_metrics(open_session)


@app.get(BASE_URI + "/{user_id}")
async def get_goals(user_id: str,
                    session: Session = Depends(get_db)):
    """Return all goals in database."""
    with session as open_session:
        return get_user_goals(session=open_session, user_id=user_id)


@app.delete(BASE_URI + "/{goal_id}")
async def delete_user_goal(goal_id: int, session: Session = Depends(get_db)):
    """Delete goal with goal_id."""
    if get_goal(session, goal_id) is None:
        raise HTTPException(status_code=404, detail="No such goal")
    with session as open_session:
        delete_goal(session=open_session, goal_id=goal_id)


@app.patch(BASE_URI + "/{goal_id}")
async def _update_goal(goal_update: GoalUpdate,
                       goal_id: int, session: Session = Depends(get_db)):
    """Update goal with goal_id."""
    with session as open_session:
        if get_goal(open_session, goal_id=goal_id) is None:
            raise HTTPException(status_code=404, detail="No such goal")
        update_goal(session, goal_id, goal_update)
    return JSONResponse(content={}, status_code=200)
