# pylint: disable= missing-module-docstring, missing-function-docstring
# pylint: disable= unused-argument, redefined-outer-name
import pytest

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from goals.database.data import initialize_db
from goals.main import app, get_db, BASE_URI
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
    response = client.post(BASE_URI + "/1", json=goal_1)
    assert response.status_code == 200
    assert response.json() == 1


def test_several_goals_return_expected_ids(test_db):
    post_response_1 = client.post(BASE_URI + "/1", json=goal_1)
    post_response_2 = client.post(BASE_URI + "/1", json=goal_2)
    post_response_3 = client.post(BASE_URI + "/1", json=goal_3)
    assert post_response_1.json() == 1
    assert post_response_2.json() == 2
    assert post_response_3.json() == 3


def test_can_get_goal_with_user_id(test_db):
    client.post(BASE_URI + "/1", json=goal_1)
    client.post(BASE_URI + "/1?goal_id=1")
    get_response = client.get(BASE_URI + "/1")
    assert get_response.status_code == 200
    dict2 = goal_1
    dict2.update({"progress": 0})
    assert equal_dicts(get_response.json()[0], dict2, {"id", "unit"})


def test_can_get_available_metrics(test_db):
    get_response = client.get(BASE_URI + "/metrics")
    assert get_response.status_code == 200
    assert len(get_response.json()) == 3


def test_cant_delete_nonexistent_goal(test_db):
    delete = client.delete(BASE_URI + "/32")
    assert delete.status_code == 404


def test_can_delete_existent_goal(test_db):
    post_response = client.post(BASE_URI + "/1", json=goal_1)
    _id = post_response.json()
    delete = client.delete(BASE_URI + "/" + str(_id))
    assert delete.status_code == 200
    get_response = client.get(BASE_URI + "/1")
    assert get_response.json() == []


def test_modified_goal_returns_expected_data(test_db):
    post_response = client.post(BASE_URI + "/1", json=goal_3)
    _id = post_response.json()
    client.patch(BASE_URI + "/" + str(_id), json=new_goal_3)
    get_response = client.get(BASE_URI + "/1")
    assert get_response.json()[0] == updated_goal_3 | {"id": _id}
