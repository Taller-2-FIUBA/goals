"""Requests handlers."""
import os
import time

import sentry_sdk
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from environ import to_config
from prometheus_client import start_http_server, Counter
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from goals.config import AppConfig
from goals.database.crud import create_goal, get_user_goals, get_goal, \
    get_all_metrics, delete_goal, update_goal, correct_user_id
from goals.database.data import initialize_db
from goals.database.models import Base
from goals.database.initialization import get_database_url
from goals.healthcheck import HealthCheckDto
from goals.schemas import GoalBase, GoalUpdate
from goals.util import get_credentials, upload_image, download_image

BASE_URI = "/goals"
REQUEST_COUNTER = Counter(
    "my_failures", "Description of counter", ["endpoint", "http_verb"]
)
CONFIGURATION = to_config(AppConfig)
START = time.time()

start_http_server(CONFIGURATION.prometheus_port)

if CONFIGURATION.sentry.enabled:
    sentry_sdk.init(dsn=CONFIGURATION.sentry.dsn, traces_sample_rate=0.5)

app = FastAPI()


def get_db() -> Session:
    """Create a session."""
    return Session(autocommit=False, autoflush=False, bind=ENGINE)


ENGINE = create_engine(get_database_url(CONFIGURATION))
if "TESTING" not in os.environ:
    Base.metadata.create_all(bind=ENGINE)
    initialize_db(get_db())


@app.post(BASE_URI + "/{user_id}")
async def add_goal_for_user(request: Request,
                            goal: GoalBase, user_id: int,
                            session: Session = Depends(get_db)):
    """Create a new goal for user_id."""
    creds = await get_credentials(request)
    if creds["id"] != user_id:
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        goal_id = create_goal(session=open_session, goal=goal, user_id=user_id)
        if goal.image:
            await upload_image(goal.image, user_id, goal_id)
        return goal_id


@app.get(BASE_URI + "/metrics")
async def get_metrics(request: Request,
                      session: Session = Depends(get_db)):
    """Return all metrics in database."""
    creds = await get_credentials(request)
    if not creds["role"] == "admin" and not creds["role"] == "user":
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        return get_all_metrics(open_session)


@app.get(BASE_URI + "/{user_id}")
async def get_goals(request: Request, user_id: int,
                    session: Session = Depends(get_db)):
    """Return all goals in database."""
    creds = await get_credentials(request)
    if creds["id"] != user_id:
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        user_goals = get_user_goals(session=open_session, user_id=user_id)
        for _idx, user_goal in enumerate(user_goals):
            image = await download_image(user_id, user_goal["id"])
            if image:
                user_goal.update(image)
        return user_goals


@app.delete(BASE_URI + "/{goal_id}")
async def delete_user_goal(request: Request,
                           goal_id: int, session: Session = Depends(get_db)):
    """Delete goal with goal_id."""
    creds = await get_credentials(request)
    if get_goal(session, goal_id) is None:
        raise HTTPException(status_code=404, detail="No such goal")
    if correct_user_id(session, goal_id, creds["id"]) is False:
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        delete_goal(session=open_session, goal_id=goal_id)


@app.patch(BASE_URI + "/{goal_id}")
async def _update_goal(request: Request, goal_update: GoalUpdate,
                       goal_id: int, session: Session = Depends(get_db)):
    """Update goal with goal_id."""
    creds = await get_credentials(request)
    if get_goal(session, goal_id) is None:
        raise HTTPException(status_code=404, detail="No such goal")
    if correct_user_id(session, goal_id, creds["id"]) is False:
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        update_goal(open_session, goal_id, goal_update)
    return JSONResponse(content={}, status_code=200)


@app.get(BASE_URI + "/healthcheck/")
async def health_check() -> HealthCheckDto:
    """Check for how long has the service been running."""
    return HealthCheckDto(uptime=time.time() - START)
