
from contextlib import asynccontextmanager
from unittest.mock import patch, Mock

import httpx
import pytest
from fastapi.testclient import TestClient

from main import app, get_db
from database import Base
from test_database import TestSessionLocal, test_engine
from models import Monitor, MonitorResult


# Disable the real scheduler during tests
@asynccontextmanager
async def pulsecheck_test_lifespan(app):
    yield


app.router.lifespan_context = pulsecheck_test_lifespan


# Use the separate test database
def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


# Reset test data before each test
@pytest.fixture(autouse=True)
def reset_test_database():
    Base.metadata.create_all(bind=test_engine)

    with test_engine.begin() as connection:
        connection.execute(MonitorResult.__table__.delete())
        connection.execute(Monitor.__table__.delete())

    yield


# 1. Test home endpoint
def test_home_endpoint():
    with TestClient(app) as client:
        response = client.get("/")

    assert response.status_code == 200
    assert response.json()["message"] == "PulseCheck API is running!"


# 2. Test API documentation
def test_api_docs_available():
    with TestClient(app) as client:
        response = client.get("/docs")

    assert response.status_code == 200


# 3. Test healthy API response
def test_check_healthy_api():
    mock_response = Mock()
    mock_response.status_code = 200

    with patch("main.httpx.get", return_value=mock_response):
        with TestClient(app) as client:
            response = client.post(
                "/check",
                json={"url": "https://example.com"}
            )

    assert response.status_code == 200
    assert response.json()["is_healthy"] is True
    assert response.json()["status_code"] == 200


# 4. Test unhealthy API response
def test_check_unhealthy_api():
    mock_response = Mock()
    mock_response.status_code = 500

    with patch("main.httpx.get", return_value=mock_response):
        with TestClient(app) as client:
            response = client.post(
                "/check",
                json={"url": "https://example.com"}
            )

    assert response.status_code == 200
    assert response.json()["is_healthy"] is False
    assert response.json()["status_code"] == 500


# 5. Test connection failure
def test_check_connection_failure():
    with patch(
        "main.httpx.get",
        side_effect=httpx.ConnectError("Connection failed")
    ):
        with TestClient(app) as client:
            response = client.post(
                "/check",
                json={"url": "https://example.com"}
            )

    assert response.status_code == 200
    assert response.json()["is_healthy"] is False
    assert response.json()["status_code"] is None


# 6. Test timeout
def test_check_timeout():
    with patch(
        "main.httpx.get",
        side_effect=httpx.TimeoutException("Request timed out")
    ):
        with TestClient(app) as client:
            response = client.post(
                "/check",
                json={"url": "https://example.com"}
            )

    assert response.status_code == 200
    assert response.json()["is_healthy"] is False
    assert response.json()["status_code"] is None


# 7. Test duplicate monitor registration
def test_duplicate_monitor_registration():
    monitor = {
        "name": "Test Monitor",
        "url": "https://example.com"
    }

    with TestClient(app) as client:
        first_response = client.post("/monitors", json=monitor)
        second_response = client.post("/monitors", json=monitor)

    assert first_response.status_code == 200
    assert second_response.status_code == 409


# 8. Test invalid URL
def test_check_invalid_url():
    with TestClient(app) as client:
        response = client.post(
            "/check",
            json={"url": "not-a-valid-url"}
        )

    assert response.status_code == 422


# 9. Test summary endpoint
def test_summary_endpoint():
    with TestClient(app) as client:
        response = client.get("/summary")

    assert response.status_code == 200

    data = response.json()

    assert "total_checks" in data
    assert "successful_checks" in data
    assert "failed_checks" in data
    assert "uptime_percentage" in data


# 10. Test summary calculations
def test_summary_calculation_is_valid():
    with TestClient(app) as client:
        response = client.get("/summary")

    assert response.status_code == 200

    data = response.json()

    total = data["total_checks"]
    successful = data["successful_checks"]
    failed = data["failed_checks"]
    percentage = data["uptime_percentage"]

    assert total == successful + failed
    assert 0 <= successful <= total
    assert 0 <= failed <= total
    assert 0 <= percentage <= 100

    if total > 0:
        expected = round((successful / total) * 100, 2)
        assert percentage == expected
    else:
        assert percentage == 0
