"""Requests handlers."""
import logging
import os
import time
from typing import Optional

import sentry_sdk
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from fastapi.applications import get_swagger_ui_html
from fastapi.middleware.cors import CORSMiddleware
from environ import to_config
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from newrelic.agent import (
    record_custom_metric as record_metric,
    register_application,
)

from goals.config import AppConfig
from goals.database.crud import create_goal, get_user_goals, get_goal, \
    get_all_metrics, delete_goal, update_goal, correct_user_id, \
    new_metric_record, get_general_progress
from goals.database.data import initialize_db
from goals.database.models import Base
from goals.database.initialization import get_database_url
from goals.healthcheck import HealthCheckDto
from goals.schemas import GoalBase, GoalUpdate
from goals.util import get_credentials, upload_image, download_image

BASE_URI = "/goals"
DOCUMENTATION_URI = BASE_URI + "/documentation/"
CONFIGURATION = to_config(AppConfig)
START = time.time()
METHODS = [
    "GET",
    "get",
    "POST",
    "post",
    "PUT",
    "put",
    "PATCH",
    "patch",
    "OPTIONS",
    "options",
    "DELETE",
    "delete",
    "HEAD",
    "head",
]
ORIGIN_REGEX = "(http)?(s)?(://)?(.*vercel.app|localhost|local)(:3000)?.*"
NR_APP = register_application()
COUNTER = {"count": 1}

logging.basicConfig(encoding="utf-8", level=CONFIGURATION.log_level.upper())

if CONFIGURATION.sentry.enabled:
    sentry_sdk.init(dsn=CONFIGURATION.sentry.dsn, traces_sample_rate=0.5)

app = FastAPI(
    debug=CONFIGURATION.log_level.upper() == "DEBUG",
    openapi_url=DOCUMENTATION_URI + "openapi.json",
)
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=METHODS,
    allow_headers=['*']
)


def get_db() -> Session:
    """Create a session."""
    return Session(autocommit=False, autoflush=False, bind=ENGINE)


ENGINE = create_engine(get_database_url(CONFIGURATION))
if "TESTING" not in os.environ:
    Base.metadata.create_all(bind=ENGINE)
    logging.info("Initializing database...")
    initialize_db(get_db())


@app.post(BASE_URI + "/{user_id}")
async def add_goal_for_user(request: Request,
                            goal: GoalBase, user_id: int,
                            session: Session = Depends(get_db)):
    """Create a new goal for user_id."""
    record_metric('Custom/goals-userId/post', COUNTER, NR_APP)
    logging.info("Adding goal %s for user %s", goal.__dict__, user_id)
    creds = await get_credentials(request)
    if creds["id"] != user_id:
        logging.warning("User %s has invalid credentials %s", user_id, creds)
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        logging.info("Creating goals...")
        goal_id = create_goal(session=open_session, goal=goal, user_id=user_id)
        if goal.image:
            logging.info("Uploading goal image...")
            await upload_image(goal.image, user_id, goal_id)
        return goal_id


@app.get(BASE_URI + "/metrics")
async def get_metrics(request: Request,
                      session: Session = Depends(get_db)):
    """Return all metrics in database."""
    record_metric('Custom/goals-metrics/get', COUNTER, NR_APP)
    logging.info("Returning all metrics...")
    creds = await get_credentials(request)
    if not creds["role"] == "admin" and not creds["role"] == "user":
        logging.warning("User is not authorized to get metrics: %s", creds)
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        return get_all_metrics(open_session)


@app.get(BASE_URI + "/{user_id}/metricsProgress/{metric}")
async def get_metrics_progress(request: Request,
                               user_id: int,
                               metric: str,
                               session: Session = Depends(get_db),
                               days: Optional[int] = 7,
                               ):
    """Create a new goal for user_id."""
    record_metric(
        'Custom/goals-userId-metricsProgress-metric/get', COUNTER, NR_APP
    )
    logging.info("Requesting  %s progress for user %s", metric, user_id)
    creds = await get_credentials(request)
    if creds["id"] != user_id:
        logging.warning("User %s has invalid credentials %s", user_id, creds)
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        breakdown = get_general_progress(session=open_session,
                                         metric=metric,
                                         user_id=user_id,
                                         days=days)
        if breakdown is None:
            raise HTTPException(status_code=404,
                                detail="No data found on that specific metric")
        body = {
            "progress": breakdown
        }
        return JSONResponse(content=body, status_code=200)


@app.get(BASE_URI + "/{user_id}")
async def get_goals(request: Request, user_id: int,
                    session: Session = Depends(get_db)):
    """Return all goals in database."""
    record_metric('Custom/goals-userId/get', COUNTER, NR_APP)
    logging.info("Returning all goals...")
    creds = await get_credentials(request)
    if creds["id"] != user_id:
        logging.warning("User %s has invalid credentials %s", user_id, creds)
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        user_goals = get_user_goals(session=open_session, user_id=user_id)
        logging.info("Downloading images for goals...")
        for _idx, user_goal in enumerate(user_goals):
            logging.debug("Downloading image for goal %s...", user_goal["id"])
            image = await download_image(user_id, user_goal["id"])
            if image:
                user_goal.update(image)
        return user_goals


@app.delete(BASE_URI + "/{goal_id}")
async def delete_user_goal(request: Request,
                           goal_id: int, session: Session = Depends(get_db)):
    """Delete goal with goal_id."""
    record_metric('Custom/goals-goalId/delete', COUNTER, NR_APP)
    logging.info("Deleting goal %s...", goal_id)
    creds = await get_credentials(request)
    if get_goal(session, goal_id) is None:
        raise HTTPException(status_code=404, detail="No such goal")
    if correct_user_id(session, goal_id, creds["id"]) is False:
        logging.warning("User has invalid credentials %s", creds)
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        delete_goal(session=open_session, goal_id=goal_id)


@app.patch(BASE_URI + "/{goal_id}")
async def _update_goal(request: Request, goal_update: GoalUpdate,
                       goal_id: int, session: Session = Depends(get_db)):
    """Update goal with goal_id."""
    record_metric('Custom/goals-goalId/patch', COUNTER, NR_APP)
    logging.info("Updating goal %s with %s...", goal_id, goal_update.__dict__)
    creds = await get_credentials(request)
    if get_goal(session, goal_id) is None:
        raise HTTPException(status_code=404, detail="No such goal")
    if correct_user_id(session, goal_id, creds["id"]) is False:
        logging.warning("User has invalid credentials %s", creds)
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        progress_delta = update_goal(open_session, goal_id, goal_update)
        if goal_update.progress is not None:
            new_metric_record(open_session, goal_id, progress_delta)
    return JSONResponse(content={}, status_code=200)


@app.get(BASE_URI + "/healthcheck/")
async def health_check() -> HealthCheckDto:
    """Check for how long has the service been running."""
    return HealthCheckDto(uptime=time.time() - START)


@app.get(DOCUMENTATION_URI, include_in_schema=False)
async def custom_swagger_ui_html(req: Request):
    """To show Swagger with API documentation."""
    root_path = req.scope.get("root_path", "").rstrip("/")
    openapi_url = root_path + app.openapi_url
    return get_swagger_ui_html(
        openapi_url=openapi_url,
        title="FIUFIT goals",
    )
