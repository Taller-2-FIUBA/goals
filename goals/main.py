"""Requests handlers."""
from fastapi import Depends, FastAPI
from environ import to_config
from prometheus_client import start_http_server, Counter
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from goals.config import AppConfig
from goals.database.crud import create_goal, get_all_goals
from goals.database.models import Base
from goals.database.initialization import get_database_url
from goals.schemas import GoalBase

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


@app.post(BASE_URI)
async def new_goal(goal: GoalBase, session: Session = Depends(get_db)):
    """Create a new goal."""
    with session as open_session:
        return create_goal(session=open_session, goal=goal)


@app.get(BASE_URI)
async def get_goals(session: Session = Depends(get_db)):
    """Return all goals in database."""
    with session as open_session:
        return get_all_goals(session=open_session)
