from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

import src.app as app_module


@pytest.fixture
def reset_activities():
    """Restore the in-memory activities state before and after each test."""
    original = deepcopy(app_module.activities)
    try:
        yield
    finally:
        app_module.activities.clear()
        app_module.activities.update(original)


def test_root_redirects_to_static_index(reset_activities):
    # Arrange
    client = TestClient(app_module.app)

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_catalog(reset_activities):
    # Arrange
    client = TestClient(app_module.app)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
    assert payload["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_successfully_adds_student(reset_activities):
    # Arrange
    client = TestClient(app_module.app)
    email = "newstudent@mergington.edu"

    # Act
    response = client.post("/activities/Basketball/signup", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for Basketball"}
    assert email in app_module.activities["Basketball"]["participants"]


def test_signup_rejects_duplicate_email(reset_activities):
    # Arrange
    client = TestClient(app_module.app)
    email = "michael@mergington.edu"

    # Act
    response = client.post("/activities/Chess Club/signup", params={"email": email})

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Already signed up for Chess Club"}


def test_signup_returns_404_for_unknown_activity(reset_activities):
    # Arrange
    client = TestClient(app_module.app)

    # Act
    response = client.post("/activities/Unknown Club/signup", params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_successfully_removes_student(reset_activities):
    # Arrange
    client = TestClient(app_module.app)
    email = "michael@mergington.edu"

    # Act
    response = client.delete("/activities/Chess Club/participants", params={"email": email})

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from Chess Club"}
    assert email not in app_module.activities["Chess Club"]["participants"]


def test_unregister_returns_404_for_unknown_email(reset_activities):
    # Arrange
    client = TestClient(app_module.app)
    email = "notregistered@mergington.edu"

    # Act
    response = client.delete("/activities/Chess Club/participants", params={"email": email})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "notregistered@mergington.edu is not signed up for Chess Club"}


def test_unregister_returns_404_for_unknown_activity(reset_activities):
    # Arrange
    client = TestClient(app_module.app)

    # Act
    response = client.delete("/activities/Unknown Club/participants", params={"email": "student@mergington.edu"})

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}
