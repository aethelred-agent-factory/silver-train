# tests/test_governance/test_approval_workflow.py
from datetime import datetime, timedelta

import pytest
from src.governance.approval_workflow import ApprovalWorkflow
from src.storage.state_manager import StateManager


@pytest.fixture
def approval_workflow(test_config, in_memory_state_manager):
    return ApprovalWorkflow(test_config, in_memory_state_manager)


def test_request_approval(approval_workflow, in_memory_state_manager):
    incident_id = "inc_abc"
    description = "Critical bug fix"
    ticket_id = approval_workflow.request_approval(incident_id, description)

    assert ticket_id is not None

    # Verify in DB
    ticket = in_memory_state_manager.execute_query(
        "SELECT * FROM approval_tickets WHERE ticket_id = ?", (ticket_id,), fetch="one"
    )
    assert ticket is not None
    assert ticket[1] == incident_id
    assert ticket[3].startswith(
        datetime.utcnow().isoformat()[:10]
    )  # Date part should match
    assert ticket[6] == "pending"


def test_approve_ticket(approval_workflow, in_memory_state_manager):
    ticket_id = approval_workflow.request_approval("inc_def", "Urgent parameter change")

    approved = approval_workflow.approve_ticket(ticket_id, "test_approver")
    assert approved is True

    ticket = in_memory_state_manager.execute_query(
        "SELECT * FROM approval_tickets WHERE ticket_id = ?", (ticket_id,), fetch="one"
    )
    assert ticket[6] == "approved"
    assert ticket[4] == "test_approver"
    assert ticket[5] is not None  # approved_at should be set


def test_reject_ticket(approval_workflow, in_memory_state_manager):
    ticket_id = approval_workflow.request_approval("inc_ghi", "New strategy deployment")

    rejected = approval_workflow.reject_ticket(ticket_id, "test_rejector")
    assert rejected is True

    ticket = in_memory_state_manager.execute_query(
        "SELECT * FROM approval_tickets WHERE ticket_id = ?", (ticket_id,), fetch="one"
    )
    assert ticket[6] == "rejected"
    assert ticket[4] == "test_rejector"


def test_check_approval_status(approval_workflow, in_memory_state_manager):
    ticket_id_pending = approval_workflow.request_approval("inc_jkl", "Test pending")
    ticket_id_approved = approval_workflow.request_approval("inc_mno", "Test approved")
    approval_workflow.approve_ticket(ticket_id_approved, "tester")

    assert approval_workflow.check_approval_status(ticket_id_pending) == "pending"
    assert approval_workflow.check_approval_status(ticket_id_approved) == "approved"
    assert approval_workflow.check_approval_status("non_existent") is None


def test_check_approval_status_expired(approval_workflow, in_memory_state_manager):
    # Request approval with a very short timeout
    ticket_id = approval_workflow.request_approval(
        "inc_pqr", "Test expired", timeout_hours=-1
    )

    # Simulate time passing by checking after the timeout
    status = approval_workflow.check_approval_status(ticket_id)
    assert status == "expired"

    # Verify in DB that status was updated
    ticket = in_memory_state_manager.execute_query(
        "SELECT status FROM approval_tickets WHERE ticket_id = ?",
        (ticket_id,),
        fetch="one",
    )
    assert ticket[0] == "expired"
