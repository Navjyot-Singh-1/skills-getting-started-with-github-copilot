import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture(autouse=True)
def reset_app_state():
    app_module.reset_activities()
    yield
    app_module.reset_activities()


@pytest.fixture
def client():
    with TestClient(app_module.app) as test_client:
        yield test_client


def test_list_activities_returns_seed_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    body = response.json()
    assert "Chess Club" in body
    assert body["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_new_participant(client):
    response = client.post(
        "/activities/Chess Club/signup?email=student@mergington.edu"
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Signed up student@mergington.edu for Chess Club"
    assert "student@mergington.edu" in app_module.activities["Chess Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    response = client.post(
        "/activities/Chess Club/signup?email=michael@mergington.edu"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_signup_rejects_when_activity_is_full(client):
    activity = app_module.activities["Chess Club"]
    activity["participants"] = [f"student{i}@mergington.edu" for i in range(12)]
    activity["max_participants"] = 12

    response = client.post(
        "/activities/Chess Club/signup?email=extra@mergington.edu"
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Activity is full"


def test_unregister_participant_removes_email_from_activity(client):
    response = client.post(
        "/activities/Chess Club/unregister?email=michael@mergington.edu"
    )

    assert response.status_code == 200
    assert response.json()["message"] == "Unregistered michael@mergington.edu from Chess Club"

    activities_response = client.get("/activities")
    activity = activities_response.json()["Chess Club"]
    assert "michael@mergington.edu" not in activity["participants"]
