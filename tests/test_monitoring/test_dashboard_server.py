
import pytest
from httpx import AsyncClient
from governance.incident_tracker import IncidentTracker
from monitoring.dashboard_server import DashboardServer
from storage.artifact_manager import ArtifactManager
from storage.state_manager import StateManager


@pytest.fixture(scope="function")
def mock_state_manager(mocker):
    mock = mocker.Mock(spec=StateManager)
    # Add any necessary mock methods, e.g., execute_query for incident_tracker
    mock.execute_query.return_value = []  # Default for empty
    return mock


@pytest.fixture(scope="function")
def mock_artifact_manager(mocker):
    mock = mocker.Mock(spec=ArtifactManager)
    mock.download_artifact.return_value = '{"test": "artifact_content"}'
    return mock


@pytest.fixture(scope="function")
def mock_incident_tracker(mocker):
    mock = mocker.Mock(spec=IncidentTracker)
    mock.get_active_incidents.return_value = [("inc1", "type1", "details1")]
    return mock


@pytest.fixture(scope="function")
def dashboard_app(
    test_config, mock_state_manager, mock_artifact_manager, mock_incident_tracker
):
    # Temporarily set port to avoid conflicts if running multiple tests
    test_config["system_config"]["monitoring"]["dashboard_port"] = 8001
    server = DashboardServer(
        test_config, mock_state_manager, mock_artifact_.pyManager, mock_incident_tracker
    )
    return server.app


from fastapi.testclient import TestClient


@pytest.mark.asyncio
async def test_read_root(dashboard_app):
    with TestClient(dashboard_app) as client:
        response = client.get("/")
        assert response.status_code == 200
        assert "Welcome to the Strategy Optimizer Dashboard!" in response.text


@pytest.mark.asyncio
async def test_get_metrics(dashboard_app):
    with TestClient(dashboard_app) as client:
        response = client.get("/metrics")
        assert response.status_code == 200
        assert response.json() == {
            "status": "ok",
            "equity": 100000,
            "drawdown": 5.2,
            "t1_flags": 0,
        }


@pytest.mark.asyncio
async def test_get_incidents(dashboard_app, mock_incident_tracker):
    with TestClient(dashboard_app) as client:
        response = client.get("/incidents")
        assert response.status_code == 200
        assert response.json() == {"active_incidents": [["inc1", "type1", "details1"]]}
        mock_incident_tracker.get_active_incidents.assert_called_once()


@pytest.mark.asyncio
async def test_get_audit_artifact(dashboard_app, mock_artifact_manager):
    with TestClient(dashboard_app) as client:
        response = client.get("/audit-artifacts/test_audit_id")
        assert response.status_code == 200
        assert response.json() == {"artifact_content": '{"test": "artifact_content"}'}
        mock_artifact_manager.download_artifact.assert_called_once_with(
            "audit_test_audit_id.json"
        )


@pytest.mark.asyncio
async def test_get_audit_artifact_not_found(dashboard_app, mock_artifact_manager):
    mock_artifact_manager.download_artifact.return_value = None  # Simulate not found
    with TestClient(dashboard_app) as client:
        response = client.get("/audit-artifacts/non_existent")
        assert response.status_code == 404
        assert response.json() == {"detail": "Artifact not found"}
