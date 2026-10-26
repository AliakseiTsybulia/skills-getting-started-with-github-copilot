from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


INITIAL_ACTIVITIES = deepcopy(app_module.activities)
ACTIVITY_NAME = "Chess Club"
NEW_STUDENT = "student@mergington.edu"
EXISTING_STUDENT = "michael@mergington.edu"


@pytest.fixture(autouse=True)
def isolate_activity_state(monkeypatch):
    monkeypatch.setattr(app_module, "activities", deepcopy(INITIAL_ACTIVITIES))


@pytest.fixture
def client():
    return TestClient(app_module.app)


def test_get_activities_returns_all_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json() == INITIAL_ACTIVITIES


def test_signup_adds_student_to_activity(client):
    response = client.post(
        f"/activities/{ACTIVITY_NAME}/signup",
        params={"email": NEW_STUDENT},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {NEW_STUDENT} for {ACTIVITY_NAME}"
    }
    assert NEW_STUDENT in client.get("/activities").json()[ACTIVITY_NAME]["participants"]


def test_signup_for_unknown_activity_returns_404(client):
    response = client.post(
        "/activities/Unknown%20Activity/signup",
        params={"email": NEW_STUDENT},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_duplicate_signup_returns_400(client):
    response = client.post(
        f"/activities/{ACTIVITY_NAME}/signup",
        params={"email": EXISTING_STUDENT},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student already signed up for this activity"
    }


def test_signup_without_email_returns_422(client):
    response = client.post(f"/activities/{ACTIVITY_NAME}/signup")

    assert response.status_code == 422


def test_unregister_removes_student_from_activity(client):
    response = client.delete(
        f"/activities/{ACTIVITY_NAME}/participants",
        params={"email": EXISTING_STUDENT},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {EXISTING_STUDENT} from {ACTIVITY_NAME}"
    }
    assert (
        EXISTING_STUDENT
        not in client.get("/activities").json()[ACTIVITY_NAME]["participants"]
    )


def test_unregister_from_unknown_activity_returns_404(client):
    response = client.delete(
        "/activities/Unknown%20Activity/participants",
        params={"email": NEW_STUDENT},
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_nonparticipant_returns_404(client):
    response = client.delete(
        f"/activities/{ACTIVITY_NAME}/participants",
        params={"email": NEW_STUDENT},
    )

    assert response.status_code == 404
    assert response.json() == {
        "detail": "Student is not signed up for this activity"
    }


def test_unregister_without_email_returns_422(client):
    response = client.delete(f"/activities/{ACTIVITY_NAME}/participants")

    assert response.status_code == 422
