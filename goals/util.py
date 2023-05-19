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
