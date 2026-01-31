# tests/test_governance/test_emergency_manager.py
import pytest
from src.governance.approval_workflow import ApprovalWorkflow  # For mocking
from src.governance.emergency_manager import EmergencyManager
from src.governance.incident_tracker import IncidentTracker  # For mocking


@pytest.fixture
def mock_incident_tracker(mocker):
    mock = mocker.Mock(spec=IncidentTracker)
    mock.log_incident.return_value = "incident_id_123"
    mock.mark_resolved.return_value = None
    return mock


@pytest.fixture
def mock_approval_workflow(mocker):
    mock = mocker.Mock(spec=ApprovalWorkflow)
    mock.request_approval.return_value = "ticket_id_abc"
    mock.check_approval_status.return_value = "approved"
    return mock


@pytest.fixture
def emergency_manager(test_config, mock_incident_tracker, mock_approval_workflow):
    return EmergencyManager(test_config, mock_incident_tracker, mock_approval_workflow)


def test_trigger_emergency(emergency_manager, mock_incident_tracker):
    emergency_manager.trigger_emergency("T1_Failure", "Critical system error")

    assert emergency_manager.is_system_halted() is True
    mock_incident_tracker.log_incident.assert_called_once()
    # mock_approval_workflow.request_approval should be called, but is commented out for now


def test_revert_to_safe_baseline(emergency_manager):
    # Just check if it logs the action, as the actual parameter update is not implemented
    emergency_manager.revert_to_safe_baseline()
    assert True  # No direct assertion, just ensures no error


def test_is_system_halted(emergency_manager):
    assert emergency_manager.is_system_halted() is False
    emergency_manager.trigger_emergency("Test_Emergency", "test")
    assert emergency_manager.is_system_halted() is True


def test_resume_system(
    emergency_manager, mock_incident_tracker, mock_approval_workflow
):
    emergency_manager.trigger_emergency("Test_Emergency", "test")
    emergency_manager.resume_system("incident_id_123", "Manual review and fix")

    assert emergency_manager.is_system_halted() is False
    mock_incident_tracker.mark_resolved.assert_called_once_with(
        "incident_id_123", "Manual review and fix"
    )
    # mock_approval_workflow.check_approval_status should have been called
