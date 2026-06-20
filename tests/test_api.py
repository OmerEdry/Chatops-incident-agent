# tests/test_api.py
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient

from src.db.models import IncidentSeverity
from src.main import app
from src.services.schemas import DeepAnalysisResult, IncidentAnalysisResult

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def client():
    """TestClient with DB startup bypassed."""
    with patch("src.main.init_db", new_callable=AsyncMock):
        with TestClient(app) as c:
            yield c


_MOCK_RESULT_P2 = IncidentAnalysisResult(
    summary="High CPU on prod-api-01",
    severity=IncidentSeverity.P2_HIGH,
    reasoning="Sustained CPU above 95% for 10 minutes.",
    routed_to_claude=True,
    deep_analysis=DeepAnalysisResult(
        root_cause="Runaway process after deploy.",
        recommended_actions=["Restart the process", "Roll back deploy"],
        confidence="medium",
    ),
)

_MOCK_RESULT_P4 = IncidentAnalysisResult(
    summary="Scheduled job completed",
    severity=IncidentSeverity.P4_INFO,
    reasoning="Routine informational event.",
    routed_to_claude=False,
    deep_analysis=None,
)

# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

def test_health_returns_200(client):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "chatops-agent"}


# ---------------------------------------------------------------------------
# POST /api/v1/webhooks/incident — success paths
# ---------------------------------------------------------------------------

def test_incident_webhook_high_severity_escalates(client):
    with patch("src.api.routes.route_incident", new_callable=AsyncMock, return_value=_MOCK_RESULT_P2):
        response = client.post(
            "/api/v1/webhooks/incident",
            json={
                "source": "pagerduty",
                "incident_id": "INC-001",
                "title": "High CPU on prod-api-01",
                "description": "CPU sustained above 95% for 10 minutes",
                "raw_data": {},
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["severity"] == "P2_HIGH"
    assert body["routed_to_claude"] is True
    assert body["deep_analysis"] is not None


def test_incident_webhook_low_severity_no_escalation(client):
    with patch("src.api.routes.route_incident", new_callable=AsyncMock, return_value=_MOCK_RESULT_P4):
        response = client.post(
            "/api/v1/webhooks/incident",
            json={
                "source": "github",
                "incident_id": "INC-002",
                "title": "Scheduled job completed",
                "raw_data": {},
            },
        )

    assert response.status_code == 200
    body = response.json()
    assert body["severity"] == "P4_INFO"
    assert body["routed_to_claude"] is False
    assert body["deep_analysis"] is None


# ---------------------------------------------------------------------------
# POST /api/v1/webhooks/incident — error paths
# ---------------------------------------------------------------------------

def test_incident_webhook_service_failure_returns_503(client):
    with patch(
        "src.api.routes.route_incident",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Gemini API unavailable"),
    ):
        response = client.post(
            "/api/v1/webhooks/incident",
            json={
                "source": "github",
                "incident_id": "INC-003",
                "title": "Disk full on worker-01",
                "raw_data": {},
            },
        )

    assert response.status_code == 503
    assert "failed" in response.json()["detail"].lower()


def test_incident_webhook_missing_required_fields_returns_422(client):
    response = client.post(
        "/api/v1/webhooks/incident",
        json={"source": "github"},  # missing incident_id and title
    )
    assert response.status_code == 422


# ---------------------------------------------------------------------------
# Discord background task — notification routing
# ---------------------------------------------------------------------------

def test_discord_alert_triggered_for_p2(client):
    with patch("src.api.routes.route_incident", new_callable=AsyncMock, return_value=_MOCK_RESULT_P2):
        with patch("src.api.routes.send_discord_alert", new_callable=AsyncMock) as mock_discord:
            response = client.post(
                "/api/v1/webhooks/incident",
                json={
                    "source": "pagerduty",
                    "incident_id": "INC-004",
                    "title": "High CPU on prod-api-01",
                    "description": "CPU sustained above 95% for 10 minutes",
                    "raw_data": {},
                },
            )

    assert response.status_code == 200
    mock_discord.assert_awaited_once_with(_MOCK_RESULT_P2)


def test_discord_alert_not_triggered_for_p4(client):
    with patch("src.api.routes.route_incident", new_callable=AsyncMock, return_value=_MOCK_RESULT_P4):
        with patch("src.api.routes.send_discord_alert", new_callable=AsyncMock) as mock_discord:
            response = client.post(
                "/api/v1/webhooks/incident",
                json={
                    "source": "github",
                    "incident_id": "INC-005",
                    "title": "Scheduled job completed",
                    "raw_data": {},
                },
            )

    assert response.status_code == 200
    mock_discord.assert_not_awaited()
