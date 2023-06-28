# pylint: disable= missing-module-docstring, missing-function-docstring
# pylint: disable= missing-class-docstring
import asyncio
import pytest
from fastapi import HTTPException

from goals.util import get_name, get_auth_header, get_credentials


class Request:
    headers = {}


def test_image_name_returns_correctly():
    assert get_name(1, 3) == "user1goal3"


def test_empty_auth_header_returns_none():
    request = Request()
    setattr(request, 'headers', {})
    assert get_auth_header(request) is None


def test_auth_header_with_token_returns_token():
    request = Request()
    setattr(request, 'headers', {"Authorization": "token"})
    assert get_auth_header(request) == {"Authorization": "token"}


def test_get_credentials_raises_exception_if_theres_no_auth_header():
    request = Request()
    setattr(request, 'headers', {})
    with pytest.raises(HTTPException) as exc_info:
        asyncio.run(get_credentials(request))
    assert isinstance(exc_info.value, HTTPException)
    assert exc_info.value.status_code == 403
    assert exc_info.value.detail == "No token"
