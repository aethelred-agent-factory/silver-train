# tests/test_governance/test_incident_tracker.py
from datetime import datetime

import pytest
from src.governance.incident_tracker import IncidentTracker
from src.storage.state_manager import StateManager


@pytest.fixture
def incident_tracker(test_config, in_memory_state_manager):
    return IncidentTracker(test_config, in_memory_state_manager)


def test_log_incident(incident_tracker, in_memory_state_manager):
    incident_id = incident_tracker.log_incident(
        "T1_DataGap", "Missing critical market data", "prop_123"
    )

    assert incident_id is not None

    # Verify in DB
    incident = in_memory_state_manager.execute_query(
        "SELECT * FROM incidents WHERE incident_id = ?", (incident_id,), fetch="one"
    )
    assert incident is not None
    assert incident[1] == "T1_DataGap"
    assert incident[2] == "Missing critical market data"
    assert incident[3] == "prop_123"
    assert incident[5] == "active"


def test_mark_resolved(incident_tracker, in_memory_state_manager):
    incident_id = incident_tracker.log_incident(
        "T1_DataGap", "Missing critical market data"
    )

    incident_tracker.mark_resolved(incident_id, "Manual data backfill completed.")

    incident = in_memory_state_manager.execute_query(
        "SELECT * FROM incidents WHERE incident_id = ?", (incident_id,), fetch="one"
    )
    assert incident[5] == "resolved"
    assert incident[6] == "Manual data backfill completed."
    assert incident[7] is not None  # resolved_at should be set


def test_get_active_incidents(incident_tracker, in_memory_state_manager):
    incident_tracker.log_incident("T1_Issue1", "Details 1")
    resolved_id = incident_tracker.log_incident("T1_Issue2", "Details 2")
    incident_tracker.mark_resolved(resolved_id, "Fixed")
    incident_tracker.log_incident("T1_Issue3", "Details 3")

    active_incidents = incident_tracker.get_active_incidents()
    assert len(active_incidents) == 2
    assert all(inc[5] == "active" for inc in active_incidents)


def test_get_incident_history(incident_tracker, in_memory_state_manager):
    incident_tracker.log_incident("T1_Issue1", "Details 1")
    incident_tracker.log_incident("T1_Issue2", "Details 2")

    history = incident_tracker.get_incident_history()
    assert len(history) == 2

    # Test filtering by ID
    first_incident_id = history[0][0]
    filtered_history = incident_tracker.get_incident_history(
        incident_id=first_incident_id
    )
    assert len(filtered_history) == 1
    assert filtered_history[0][0] == first_incident_id
