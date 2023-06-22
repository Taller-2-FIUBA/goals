# pylint: disable= missing-module-docstring, missing-function-docstring
# pylint: disable= unused-argument, redefined-outer-name
from datetime import datetime
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
    equal_dicts, new_goal_3, updated_goal_3, generate_progress

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


@patch('goals.main.get_credentials')
def test_can_get_metrics_correctly_after_one_update(token_mock, test_db):
    token_mock.return_value = admin_token
    post_response = client.post(BASE_URI + "/1", json=goal_1)
    _id = post_response.json()
    client.patch(BASE_URI + "/" + str(_id), json=generate_progress(5))
    get_response = client.get(BASE_URI + "/1/metricsProgress/distance?days=1")
    assert get_response.json() == {"progress": 5}


@patch('goals.main.get_credentials')
def test_can_get_metrics_correctly_after_several_updates(token_mock, test_db):
    token_mock.return_value = admin_token
    post_response = client.post(BASE_URI + "/1", json=goal_1)
    _id = post_response.json()
    client.patch(BASE_URI + "/" + str(_id), json=generate_progress(5))
    client.patch(BASE_URI + "/" + str(_id), json=generate_progress(10))
    client.patch(BASE_URI + "/" + str(_id), json=generate_progress(20))
    get_response = client.get(BASE_URI + "/1/metricsProgress/distance?days=1")
    assert get_response.json() == {"progress": 20}


@patch('goals.main.get_credentials')
def test_can_get_several_metrics_correctly_after_updates(token_mock, test_db):
    token_mock.return_value = admin_token
    client.post(BASE_URI + "/1", json=goal_1)
    client.post(BASE_URI + "/1", json=goal_2)
    client.post(BASE_URI + "/1", json=goal_3)
    client.patch(BASE_URI + "/1", json=generate_progress(5))
    client.patch(BASE_URI + "/3", json=generate_progress(20))
    get_response1 = client.get(BASE_URI + "/1/metricsProgress/distance")
    get_response2 = client.get(BASE_URI + "/1/metricsProgress/fat")
    get_response3 = client.get(BASE_URI + "/1/metricsProgress/muscle")
    assert get_response1.json() == {"progress": 5}
    assert get_response2.json() == {"progress": 0}
    assert get_response3.json() == {"progress": 20}


@patch('goals.database.crud.current_date')
@patch('goals.main.get_credentials')
def test_can_get_several_metrics_for_a_week_correctly(token_mock,
                                                      datetime_mock,
                                                      test_db):
    token_mock.return_value = admin_token
    client.post(BASE_URI + "/1", json=goal_1)
    datetime_mock.return_value = datetime(2023, 6, 1)
    client.patch(BASE_URI + "/1", json=generate_progress(5))
    datetime_mock.return_value = datetime(2023, 6, 14)
    client.patch(BASE_URI + "/1", json=generate_progress(15))
    get_response = client.get(BASE_URI + "/1/metricsProgress/distance")
    assert get_response.json() == {"progress": 10}


@patch('goals.database.crud.current_date')
@patch('goals.main.get_credentials')
def test_can_get_several_metrics_for_time_periods_correctly(token_mock,
                                                            datetime_mock,
                                                            test_db):
    token_mock.return_value = admin_token
    url = BASE_URI + "/1/metricsProgress/distance?"
    client.post(BASE_URI + "/1", json=goal_1)
    datetime_mock.return_value = datetime(2023, 6, 1)
    client.patch(BASE_URI + "/1", json=generate_progress(5))
    datetime_mock.return_value = datetime(2023, 6, 14)
    client.patch(BASE_URI + "/1", json=generate_progress(15))
    get_response1 = client.get(url + "days=14")
    datetime_mock.return_value = datetime(2023, 6, 16)
    client.patch(BASE_URI + "/1", json=generate_progress(25))
    get_response2 = client.get(url + "days=2")
    datetime_mock.return_value = datetime(2023, 7, 16)
    client.patch(BASE_URI + "/1", json=generate_progress(50))
    get_response3 = client.get(url + "days=30")
    datetime_mock.return_value = datetime(2024, 8, 1)
    client.patch(BASE_URI + "/1", json=generate_progress(70))
    get_response4 = client.get(url + "days=365")
    assert get_response1.json() == {"progress": 15}
    assert get_response2.json() == {"progress": 20}
    assert get_response3.json() == {"progress": 35}
    assert get_response4.json() == {"progress": 20}


@patch('goals.database.crud.current_date')
@patch('goals.main.get_credentials')
def test_can_get_several_metrics_correctly_after_no_progress(token_mock,
                                                             datetime_mock,
                                                             test_db):
    token_mock.return_value = admin_token
    client.post(BASE_URI + "/1", json=goal_1)
    datetime_mock.return_value = datetime(2023, 6, 1)
    client.patch(BASE_URI + "/1", json=generate_progress(5))
    datetime_mock.return_value = datetime(2023, 6, 8)
    client.patch(BASE_URI + "/3", json=generate_progress(20))
    datetime_mock.return_value = datetime(2023, 7, 30)
    get_response = client.get(BASE_URI + "/1/metricsProgress/distance?days=30")
    assert get_response.json() == {"progress": 0}
