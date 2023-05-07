# pylint: disable= missing-module-docstring, missing-function-docstring
# pylint: disable= unused-argument, redefined-outer-name
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from goals.database.data import initialize_db
from goals.main import app, get_db, BASE_URI
from goals.database.models import Base
from tests.test_constants import goal_2, goal_3, goal_1, equal_dicts

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(
    autocommit=False, autoflush=False, bind=engine
)


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


def test_first_goal_returns_expected_id(test_db):
    response = client.post(BASE_URI, json=goal_1)
    assert response.status_code == 200
    assert response.json() == {"goal_id": 1}


def test_several_goals_return_expected_ids(test_db):
    post_response_1 = client.post(BASE_URI, json=goal_1)
    post_response_2 = client.post(BASE_URI, json=goal_2)
    post_response_3 = client.post(BASE_URI, json=goal_3)
    assert post_response_1.json() == {"goal_id": 1}
    assert post_response_2.json() == {"goal_id": 2}
    assert post_response_3.json() == {"goal_id": 3}


def test_cant_add_goal_if_goal_id_doesnt_exist(test_db):
    client.post(BASE_URI, json=goal_1)
    client.post(BASE_URI, json=goal_2)
    response = client.post(BASE_URI + "/test_user_id?goal_id=3")
    assert response.status_code == 404


def test_can_add_goal_if_goal_id_exists(test_db):
    client.post(BASE_URI, json=goal_1)
    client.post(BASE_URI, json=goal_2)
    response = client.post(BASE_URI + "/test_user_id?goal_id=2")
    assert response.status_code == 200


def test_can_get_goal_with_user_id(test_db):
    client.post(BASE_URI, json=goal_1)
    client.post(BASE_URI + "/test_user_id?goal_id=1")
    get_response = client.get(BASE_URI + "/test_user_id")
    assert get_response.status_code == 200
    dict2 = goal_1
    dict2.update({"value": 0})
    assert equal_dicts(get_response.json()[0], dict2, {"id", "unit"})


def test_can_get_available_metrics(test_db):
    get_response = client.get(BASE_URI + "/metrics")
    assert get_response.status_code == 200
    assert len(get_response.json()) == 4
