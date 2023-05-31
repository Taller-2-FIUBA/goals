# pylint: disable= missing-module-docstring, missing-function-docstring
# pylint: disable= unused-argument, redefined-outer-name
from unittest.mock import patch

import pytest
from hamcrest import assert_that, greater_than
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from goals.database.data import initialize_db
from goals.main import DOCUMENTATION_URI, app, get_db, BASE_URI, CONFIGURATION
from goals.database.models import Base
from tests.test_constants import goal_2, goal_3, goal_1, \
    equal_dicts, new_goal_3, updated_goal_3

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)

admin_token = {"role": CONFIGURATION.test.role,
               "id": CONFIGURATION.test.id}


def override_get_db():
    try:
        database = TestingSessionLocal()
        yield database
    finally:
        database.close()


@pytest.fixture
def test_db():
    Base.metadata.create_all(bind=engine)
    initialize_db(TestingSessionLocal())
    yield
    Base.metadata.drop_all(bind=engine)


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


@patch('goals.main.get_credentials')
def test_first_goal_returns_expected_id(token_mock, test_db):
    token_mock.return_value = admin_token
    response = client.post(BASE_URI + "/1", json=goal_1)
    assert response.status_code == 200
    assert response.json() == 1


@patch('goals.main.get_credentials')
def test_several_goals_return_expected_ids(token_mock, test_db):
    token_mock.return_value = admin_token
    post_response_1 = client.post(BASE_URI + "/1", json=goal_1)
    post_response_2 = client.post(BASE_URI + "/1", json=goal_2)
    post_response_3 = client.post(BASE_URI + "/1", json=goal_3)
    assert post_response_1.json() == 1
    assert post_response_2.json() == 2
    assert post_response_3.json() == 3


@patch('goals.main.download_image')
@patch('goals.main.upload_image')
@patch('goals.main.get_credentials')
def test_can_get_goal_with_user_id(token_mock, upload_mock,
                                   download_mock, test_db):
    token_mock.return_value = admin_token
    upload_mock.return_value = None
    download_mock.return_value = None
    client.post(BASE_URI + "/1", json=goal_1)
    client.post(BASE_URI + "/1?goal_id=1")
    get_response = client.get(BASE_URI + "/1")
    assert get_response.status_code == 200
    dict2 = goal_1
    dict2.update({"progress": 0})
    assert equal_dicts(get_response.json()[0], dict2, {"id", "unit"})


@patch('goals.main.download_image')
@patch('goals.main.upload_image')
@patch('goals.main.get_credentials')
def test_can_get_available_metrics(token_mock, upload_mock,
                                   download_mock, test_db):
    token_mock.return_value = admin_token
    upload_mock.return_value = None
    download_mock.return_value = None
    get_response = client.get(BASE_URI + "/metrics")
    assert get_response.status_code == 200
    assert len(get_response.json()) == 3


@patch('goals.main.get_credentials')
def test_cant_delete_nonexistent_goal(token_mock, test_db):
    token_mock.return_value = admin_token
    delete = client.delete(BASE_URI + "/32")
    assert delete.status_code == 404


@patch('goals.main.download_image')
@patch('goals.main.upload_image')
@patch('goals.main.get_credentials')
def test_can_delete_existent_goal(token_mock, upload_mock,
                                  download_mock, test_db):
    token_mock.return_value = admin_token
    upload_mock.return_value = None
    download_mock.return_value = None
    post_response = client.post(BASE_URI + "/1", json=goal_1)
    _id = post_response.json()
    delete = client.delete(BASE_URI + "/" + str(_id))
    assert delete.status_code == 200
    get_response = client.get(BASE_URI + "/1")
    assert get_response.json() == []


@patch('goals.main.download_image')
@patch('goals.main.upload_image')
@patch('goals.main.get_credentials')
def test_modified_goal_returns_expected_data(token_mock, upload_mock,
                                             download_mock, test_db):
    token_mock.return_value = admin_token
    upload_mock.return_value = None
    download_mock.return_value = None
    post_response = client.post(BASE_URI + "/1", json=goal_3)
    _id = post_response.json()
    client.patch(BASE_URI + "/" + str(_id), json=new_goal_3)
    get_response = client.get(BASE_URI + "/1")
    assert get_response.json()[0] == updated_goal_3 | {"id": _id}


def test_when_checking_healthcheck_expect_uptime_greater_than_zero():
    response = client.get("/goals/healthcheck/")
    assert response.status_code == 200, response.json()
    assert_that(response.json()["uptime"], greater_than(0))


def test_when_getting_swagger_ui_expect_200():
    response = client.get(DOCUMENTATION_URI)
    assert response.status_code == 200, response.json()


def test_when_getting_openapi_doc_expect_200():
    response = client.get(DOCUMENTATION_URI + "openapi.json")
    assert response.status_code == 200, response.json()
