"""Utility methods."""
import os

import httpx
from environ import to_config

from fastapi import Request, HTTPException

from goals.config import AppConfig

CONFIGURATION = to_config(AppConfig)


def get_auth_header(request):
    """Check existence auth header, return it or None if it doesn't exist."""
    auth_header = request.headers.get("Authorization")
    if auth_header is None:
        return None
    return {"Authorization": auth_header}


async def get_credentials(request: Request):
    """Make a request to auth service for credentials encoded in token."""
    if "TESTING" in os.environ:
        return {
            "role": CONFIGURATION.test.role,
            "id": CONFIGURATION.test.id
        }
    url = f"http://{CONFIGURATION.auth.host}/auth/credentials"
    auth_header = get_auth_header(request)
    if auth_header is None:
        raise HTTPException(status_code=403, detail="No token")
    creds = await httpx.AsyncClient().get(url, headers=auth_header)
    if creds.status_code != 200:
        raise HTTPException(status_code=creds.status_code,
                            detail=creds.json()["Message"])
    try:
        return creds.json()['data']
    except Exception as json_exception:
        msg = "Token format error"
        raise HTTPException(status_code=403,
                            detail=msg) from json_exception


def get_name(user_id, goal_id):
    """Create name with which the image will be stored in Firebase."""
    return "user" + str(user_id) + "goal" + str(goal_id)


async def upload_image(image: str, user_id: int, goal_id: int):
    """Upload image to auth service."""
    filename = get_name(user_id, goal_id)
    if "TESTING" in os.environ:
        return
    url = f"http://{CONFIGURATION.auth.host}/auth/storage/" + filename
    body = {
        "image": image
    }
    res = await httpx.AsyncClient().post(url, json=body)
    if res.status_code != 200:
        raise HTTPException(status_code=res.status_code,
                            detail=res.json()["Message"])


async def download_image(user_id: int, goal_id: int):
    """Download image from auth service."""
    if "TESTING" in os.environ:
        return None
    filename = get_name(user_id, goal_id)
    url = f"http://{CONFIGURATION.auth.host}/auth/storage/" + filename
    res = await httpx.AsyncClient().get(url)
    if res.status_code != 200:
        return None
    return res.json()
